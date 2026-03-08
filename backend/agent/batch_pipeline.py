"""Batch pipeline: identifies top topics and generates ONE consolidated report.

Architecture mirrors pipeline.py: each batch gets an asyncio.Queue. Events
are SSE-formatted strings. The batch task runs independently of HTTP -- client
disconnect does NOT kill it.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime

from backend.agent.report_exporter import embed_report_summary, export_report_to_markdown
from backend.agent.token_tracker import RunTokenTracker
from backend.agent.topic_identifier import identify_top_topics
from backend.database.models import Report
from backend.schemas.batch import IdentifiedTopic

logger = logging.getLogger(__name__)

# Global registry: batch_id -> asyncio.Queue of SSE event strings
_batch_queues: dict[str, asyncio.Queue] = {}

_SENTINEL = object()


def get_batch_queue(batch_id: str) -> asyncio.Queue | None:
    """Return the active queue for a batch, or None if not running."""
    return _batch_queues.get(batch_id)


async def launch_batch(batch_id: str, days_lookback: int, max_topics: int) -> asyncio.Task:
    """Launch the batch pipeline as an independent background task."""
    queue: asyncio.Queue = asyncio.Queue()
    _batch_queues[batch_id] = queue

    task = asyncio.create_task(
        _run_batch(batch_id, days_lookback, max_topics, queue),
        name=f"batch-{batch_id}",
    )
    return task


async def stream_batch_queue(batch_id: str, queue: asyncio.Queue):
    """Async generator that yields SSE strings from the batch queue until sentinel."""
    while True:
        item = await queue.get()
        if item is _SENTINEL:
            await queue.put(_SENTINEL)
            break
        yield item


async def _run_batch(
    batch_id: str,
    days_lookback: int,
    max_topics: int,
    queue: asyncio.Queue,
) -> None:
    """Core batch logic: identify topics, gather sources, produce ONE consolidated report."""
    import anthropic

    from backend.agent.prompts import build_consolidated_analysis_messages, build_system_blocks
    from backend.agent.stage_format import format_consolidated_audiences
    from backend.agent.stage_ingest import retrieve_relevant_content
    from backend.agent.stage_triangulate import triangulate_sources
    from backend.config import settings
    from backend.database.connection import SessionLocal

    tracker = RunTokenTracker()

    async def emit(event: str, data: dict) -> None:
        await queue.put(_sse(event, data))

    try:
        # --- Stage 1: Identify topics ---
        await emit("status", {"stage": "identifying_topics", "batch_id": batch_id})

        topics: list[IdentifiedTopic] = await identify_top_topics(days_lookback, max_topics)

        if not topics:
            await emit(
                "error", {"message": "No topics could be identified from recent content. Try polling RSS feeds first."}
            )
            return

        topic_dicts = [{"topic": t.topic, "domain": t.domain, "rationale": t.rationale} for t in topics]

        await emit(
            "topics_identified",
            {"topics": topic_dicts, "total": len(topics)},
        )

        # --- Stage 2: Retrieve sources for all topics ---
        await emit("status", {"stage": "ingest"})

        all_chunks: list[dict] = []
        all_past: list[dict] = []
        seen_chunk_ids: set[str] = set()

        with SessionLocal() as db:
            for topic_item in topics:
                chunks, past = retrieve_relevant_content(topic_item.topic, db, trigger_fresh_ingest=False)
                for chunk in chunks:
                    doc_id = chunk.get("metadata", {}).get("chroma_doc_id", id(chunk))
                    if doc_id not in seen_chunk_ids:
                        seen_chunk_ids.add(doc_id)
                        all_chunks.append(chunk)
                for p in past:
                    doc_id = p.get("metadata", {}).get("chroma_doc_id", id(p))
                    if doc_id not in seen_chunk_ids:
                        seen_chunk_ids.add(doc_id)
                        all_past.append(p)

        logger.info(
            "Batch ingest: %d unique chunks, %d past reports across %d topics",
            len(all_chunks),
            len(all_past),
            len(topics),
        )

        # --- Stage 3: Triangulate combined sources ---
        await emit("status", {"stage": "triangulate"})
        bias_coverage, coverage_caveat, divergence_score = triangulate_sources(all_chunks)
        if coverage_caveat:
            await emit("warning", {"message": coverage_caveat})

        # --- Stage 4: Analyze — single consolidated Claude call with streaming ---
        await emit("status", {"stage": "analyze"})

        messages = build_consolidated_analysis_messages(
            topic_dicts, all_chunks, all_past, bias_coverage, coverage_caveat
        )
        system_blocks = build_system_blocks()

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        analysis_chunks: list[str] = []

        with client.messages.stream(
            model=settings.anthropic_model,
            max_tokens=16000,
            system=system_blocks,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                analysis_chunks.append(text)
                await emit("token", {"text": text})
            final_message = stream.get_final_message()
            tracker.record_usage("analyze_consolidated", final_message.usage)

        content_en = "".join(analysis_chunks)

        # --- Stage 5: Format for audiences ---
        await emit("status", {"stage": "format"})
        content_zh_tw, content_zh_tw_elder = await format_consolidated_audiences(content_en, topic_dicts, tracker)

        # --- Stage 6: Save report ---
        topic_summary = f"Top {len(topics)} Intelligence Briefing - {datetime.now(UTC).strftime('%Y-%m-%d')}"

        source_ids = [c.get("metadata", {}).get("ingested_content_id") for c in all_chunks]
        source_ids = [s for s in source_ids if s]

        with SessionLocal() as db:
            report = Report(
                topic=topic_summary,
                domain="general",
                status="complete",
                bias_score=divergence_score,
                content_en=content_en,
                content_zh_tw=content_zh_tw,
                content_zh_tw_elder=content_zh_tw_elder,
                source_ids_json=json.dumps(source_ids),
                tokens_used=tracker.total_tokens_used,
                tokens_cached=tracker.total_tokens_cached,
                cost_usd=tracker.total_cost_usd,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            _embed_report_summary(report)
            _export_report_markdown(report)

        tracker.log_summary()

        await emit(
            "complete",
            {
                "report_id": report.id,
                "tokens_used": tracker.total_tokens_used,
                "tokens_cached": tracker.total_tokens_cached,
                "cost_usd": tracker.total_cost_usd,
            },
        )

    except Exception as exc:
        logger.exception("Batch pipeline failed: %s", exc)
        await emit("error", {"message": str(exc)})

    finally:
        await queue.put(_SENTINEL)
        _batch_queues.pop(batch_id, None)


def _embed_report_summary(report: Report) -> None:
    embed_report_summary(report)


def _export_report_markdown(report: Report) -> None:
    try:
        export_report_to_markdown(report)
    except Exception as exc:
        logger.warning("Markdown export failed for report %d: %s", report.id, exc)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
