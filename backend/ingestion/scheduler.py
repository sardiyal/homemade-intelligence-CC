"""APScheduler background jobs for automated ingestion."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database.connection import SessionLocal

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def _rss_job() -> None:
    """Poll all active RSS sources."""
    from backend.ingestion.poll_tracker import mark_poll_complete, mark_poll_start
    from backend.ingestion.rss import poll_all_active_sources

    mark_poll_start()
    with SessionLocal() as db:
        results = poll_all_active_sources(db)
        total = sum(results.values())
        logger.info("RSS poll complete: %d new articles across %d sources", total, len(results))
    mark_poll_complete(results)


def _market_job() -> None:
    """Fetch Yahoo Finance market snapshot."""
    from backend.ingestion.yahoo_finance import ingest_market_snapshot

    with SessionLocal() as db:
        count = ingest_market_snapshot(db)
        logger.info("Market snapshot: %d new data points", count)


def _fred_job() -> None:
    """Fetch FRED economic indicators."""
    from backend.ingestion.fred import ingest_fred_indicators

    with SessionLocal() as db:
        count = ingest_fred_indicators(db)
        logger.info("FRED job: %d new indicators", count)


def start_scheduler() -> AsyncIOScheduler:
    """Create and start the background scheduler."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler()

    # RSS every 30 minutes
    _scheduler.add_job(_rss_job, IntervalTrigger(minutes=30), id="rss_poll", replace_existing=True)

    # Market data every 15 minutes during market hours (always scheduled, cheap API)
    _scheduler.add_job(_market_job, IntervalTrigger(minutes=15), id="market_snapshot", replace_existing=True)

    # FRED every 4 hours
    _scheduler.add_job(_fred_job, IntervalTrigger(hours=4), id="fred_poll", replace_existing=True)

    _scheduler.start()
    _update_next_poll_time()
    logger.info("Background scheduler started (RSS:30min, Market:15min, FRED:4h)")
    return _scheduler


def _update_next_poll_time() -> None:
    """Refresh the poll tracker's next-run-time from the scheduler."""
    if _scheduler is None:
        return
    from backend.ingestion.poll_tracker import set_next_scheduled_poll

    job = _scheduler.get_job("rss_poll")
    if job and job.next_run_time:
        set_next_scheduled_poll(job.next_run_time)


def get_next_rss_poll_time():
    """Return the next scheduled RSS poll time, or None."""
    if _scheduler is None:
        return None
    job = _scheduler.get_job("rss_poll")
    return job.next_run_time if job else None


def stop_scheduler() -> None:
    """Stop the background scheduler gracefully."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped")
