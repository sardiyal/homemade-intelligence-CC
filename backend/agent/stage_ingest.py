"""Stage 1 — Retrieve relevant content via ChromaDB semantic search."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.config import settings
from backend.vector_store.chroma import query_reports, query_sources, query_sources_with_salience

logger = logging.getLogger(__name__)


def retrieve_relevant_content(
    topic: str,
    db: Session,
    domain: str = "",
    trigger_fresh_ingest: bool = True,
) -> tuple[list[dict], list[dict]]:
    """Retrieve semantically relevant source chunks and past reports.

    Uses topic-conditioned salience re-ranking (Decision 3B) when a domain is provided:
    sources tagged with matching salience_domains get a distance boost in the ranking,
    so that e.g. a 'markets' query promotes financial sources without excluding geopolitics.

    Triggers fresh RSS ingestion if last ingest was more than 30 minutes ago.

    Args:
        topic: The analysis topic string.
        db: SQLAlchemy session.
        domain: Report domain for salience re-ranking ('markets', 'energy', 'taiwan', etc.).
                Pass empty string to use plain semantic search without salience.
        trigger_fresh_ingest: Whether to auto-trigger ingestion if stale.

    Returns:
        Tuple of (source_chunks, past_reports) — each a list of ChromaDB result dicts.
    """
    if trigger_fresh_ingest:
        _maybe_trigger_ingestion(db)

    if domain:
        source_chunks = query_sources_with_salience(topic, domain=domain, n_results=settings.max_source_chunks)
        logger.info("Stage 1: using salience-aware retrieval for domain='%s'", domain)
    else:
        source_chunks = query_sources(topic, n_results=settings.max_source_chunks)

    past_reports = query_reports(topic, n_results=settings.max_past_reports)

    logger.info(
        "Stage 1 retrieval: %d source chunks, %d past reports for topic='%s'",
        len(source_chunks),
        len(past_reports),
        topic[:60],
    )
    return source_chunks, past_reports


def check_reuse_guard(topic: str) -> tuple[bool, float]:
    """Check if a very similar report was generated within the reuse window.

    Args:
        topic: Analysis topic.

    Returns:
        Tuple of (should_warn, max_similarity). should_warn=True if similarity
        exceeds threshold within the reuse window.
    """
    past = query_reports(topic, n_results=1)
    if not past:
        return False, 0.0

    top = past[0]
    # ChromaDB cosine distance: 0.0 = identical, 1.0 = orthogonal
    distance = top.get("distance", 1.0)
    similarity = 1.0 - distance

    meta = top.get("metadata", {})
    created_at_str = meta.get("created_at", "")

    if created_at_str:
        try:
            created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=UTC)
            age_hours = (datetime.now(UTC) - created_at).total_seconds() / 3600
            if age_hours > settings.reuse_window_hours:
                return False, similarity
        except ValueError:
            pass

    return similarity >= settings.reuse_similarity_threshold, similarity


def _maybe_trigger_ingestion(db: Session) -> None:
    """Trigger RSS ingestion if no content was ingested in the last 30 minutes."""
    from backend.database.models import IngestedContent

    cutoff = datetime.now(UTC) - timedelta(minutes=30)
    recent = (
        db.query(IngestedContent)
        .filter(IngestedContent.ingested_at >= cutoff, IngestedContent.is_manual == False)  # noqa: E712
        .first()
    )
    if recent is None:
        logger.info("No recent automated ingestion found — triggering RSS poll")
        try:
            from backend.ingestion.rss import poll_all_active_sources

            poll_all_active_sources(db)
        except Exception as exc:
            logger.warning("Auto-triggered RSS poll failed: %s", exc)
