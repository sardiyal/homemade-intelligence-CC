"""Manual injection and source management endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import IngestedContent, Source
from backend.ingestion.manual import inject_text, inject_url
from backend.schemas.ingestion import InjectResponse, InjectTextRequest, InjectUrlRequest, SourceStatus

router = APIRouter(prefix="/api", tags=["ingestion"])
logger = logging.getLogger(__name__)


@router.post("/inject/text", response_model=InjectResponse)
def inject_text_endpoint(request: InjectTextRequest, db: Session = Depends(get_db)):
    """Inject raw article text into the pipeline."""
    content = inject_text(
        title=request.title,
        body=request.body,
        url=request.url,
        source_id=request.source_id,
        db=db,
    )
    if content is None:
        return InjectResponse(success=False, message="Duplicate content — already ingested")
    return InjectResponse(success=True, message="Injected successfully", content_id=content.id)


@router.post("/inject/url", response_model=InjectResponse)
def inject_url_endpoint(request: InjectUrlRequest, db: Session = Depends(get_db)):
    """Fetch a URL, extract text, and inject into the pipeline."""
    content = inject_url(url=request.url, source_id=request.source_id, db=db)
    if content is None:
        return InjectResponse(success=False, message="Failed to fetch/extract URL or duplicate content")
    return InjectResponse(success=True, message="URL injected successfully", content_id=content.id)


@router.get("/sources", response_model=list[SourceStatus])
def list_sources(db: Session = Depends(get_db)):
    """List all sources with article counts."""
    sources = db.query(Source).order_by(Source.layer, Source.name).all()
    result = []
    for source in sources:
        count = db.query(IngestedContent).filter(IngestedContent.source_id == source.id).count()
        status = SourceStatus(
            id=source.id,
            name=source.name,
            feed_url=source.feed_url,
            source_type=source.source_type,
            layer=source.layer,
            bias_label=source.bias_label,
            language=source.language,
            is_active=source.is_active,
            article_count=count,
        )
        result.append(status)
    return result


@router.post("/sources/ingest")
def trigger_ingest(db: Session = Depends(get_db)):
    """Manually trigger an RSS ingestion run across all active sources."""
    try:
        from backend.ingestion.poll_tracker import mark_poll_complete, mark_poll_start
        from backend.ingestion.rss import poll_all_active_sources

        mark_poll_start()
        results = poll_all_active_sources(db)
        total = sum(results.values())
        mark_poll_complete(results)
        return {"success": True, "total_new": total, "by_source": results}
    except Exception as exc:
        logger.exception("Manual ingestion trigger failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sources/poll-status")
def get_poll_status():
    """Return current RSS polling status and per-source results from the last poll."""
    from backend.ingestion.poll_tracker import get_poll_status as _get_status
    from backend.ingestion.scheduler import get_next_rss_poll_time

    status = _get_status()

    # Refresh next-poll time from scheduler on each request
    next_run = get_next_rss_poll_time()

    return {
        "last_poll_started": status.last_poll_started.isoformat() if status.last_poll_started else None,
        "last_poll_completed": status.last_poll_completed.isoformat() if status.last_poll_completed else None,
        "last_poll_duration_seconds": status.last_poll_duration_seconds,
        "is_polling": status.is_polling,
        "total_polls": status.total_polls,
        "next_scheduled_poll": next_run.isoformat() if next_run else None,
        "results": [
            {
                "source_name": r.source_name,
                "new_articles": r.new_articles,
                "polled_at": r.polled_at.isoformat(),
            }
            for r in status.results
        ],
    }
