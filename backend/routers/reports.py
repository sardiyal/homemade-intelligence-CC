"""Report generation and retrieval endpoints."""

import asyncio
import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.agent.batch_pipeline import get_batch_queue, launch_batch, stream_batch_queue
from backend.agent.pipeline import get_event_queue, launch_pipeline, stream_queue
from backend.database.connection import SessionLocal, get_db
from backend.database.models import Report
from backend.schemas.batch import BatchGenerateRequest
from backend.schemas.report import GenerateReportRequest, ReportDetail, ReportSummary

router = APIRouter(prefix="/api/reports", tags=["reports"])
logger = logging.getLogger(__name__)


@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
):
    """Start report generation and stream SSE output.

    Creates the report record, launches the pipeline as an independent
    background task (survives client disconnect), and streams events
    from the task's queue until completion.

    Events:
    - status: pipeline stage updates
    - token: streaming analysis text
    - warning: coverage or reuse warnings
    - complete: final stats
    - error: pipeline failure
    """
    # Create the report record upfront so we can return its ID in the first event
    report = Report(
        topic=request.topic,
        domain=request.domain,
        status="generating",
        created_at=datetime.now(UTC),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    report_id = report.id

    # Launch pipeline as independent background task
    await launch_pipeline(
        report_id=report_id,
        topic=request.topic,
        domain=request.domain,
        manual_text=request.manual_text,
        manual_title=request.manual_title,
    )

    queue = get_event_queue(report_id)

    async def event_generator():
        if queue is None:
            yield 'event: error\ndata: {"message": "Pipeline failed to start"}\n\n'
            return
        async for chunk in stream_queue(report_id, queue):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("", response_model=list[ReportSummary])
def list_reports(
    domain: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List reports with optional domain and status filters."""
    q = db.query(Report)
    if domain:
        q = q.filter(Report.domain == domain)
    if status:
        q = q.filter(Report.status == status)
    return q.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/export-all")
def export_all_reports_to_markdown():
    """One-time bulk export of all completed reports to markdown files in reports/."""
    from backend.agent.report_exporter import export_all_reports

    count = export_all_reports()
    return {"exported": count}


@router.post("/generate-batch")
async def generate_batch(request: BatchGenerateRequest):
    """Identify top topics from recent content and generate reports sequentially.

    Returns an SSE stream. Events:
    - status: pipeline stage updates
    - topics_identified: {topics, total}
    - report_started: {index, total, topic, domain}
    - report_completed: {index, total, report_id, topic, domain, tokens_used, cost_usd, running_total_cost}
    - report_skipped: {index, total, topic, reason}
    - report_failed: {index, total, topic, error}
    - batch_complete: {total_reports, total_topics, total_tokens, total_cost_usd, reports}
    - error: {message}
    """
    batch_id = f"batch_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}"
    await launch_batch(batch_id, request.days_lookback, request.max_topics)
    queue = get_batch_queue(batch_id)

    async def event_generator():
        if queue is None:
            yield 'event: error\ndata: {"message": "Batch failed to start"}\n\n'
            return
        async for chunk in stream_batch_queue(batch_id, queue):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/active")
def get_active_reports(db: Session = Depends(get_db)):
    """Return reports currently being generated, with live pipeline indicator."""
    from backend.agent.pipeline import _queues

    generating = (
        db.query(Report).filter(Report.status.in_(["pending", "generating"])).order_by(Report.created_at.desc()).all()
    )
    return [
        {
            "id": r.id,
            "topic": r.topic,
            "domain": r.domain,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "has_active_pipeline": r.id in _queues,
        }
        for r in generating
    ]


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a single report with all audience versions."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


@router.get("/{report_id}/stream")
async def stream_report(report_id: int, db: Session = Depends(get_db)):
    """SSE for an in-progress report: forwards from queue if running, else polls DB."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    queue = get_event_queue(report_id)

    async def generator():
        # If pipeline is still running, forward from its queue
        if queue is not None:
            async for chunk in stream_queue(report_id, queue):
                yield chunk
            return

        # Otherwise poll DB for status
        with SessionLocal() as poll_db:
            rep = poll_db.get(Report, report_id)
            for _ in range(120):
                if rep:
                    poll_db.refresh(rep)
                    yield f"event: status\ndata: {json.dumps({'status': rep.status, 'report_id': report_id})}\n\n"
                    if rep.status in ("complete", "failed"):
                        break
                await asyncio.sleep(5)

    return StreamingResponse(generator(), media_type="text/event-stream")
