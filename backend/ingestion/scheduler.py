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


def _alpha_vantage_job() -> None:
    """Fetch Alpha Vantage market signals (VIX, equities, forex)."""
    from backend.ingestion.alpha_vantage import ingest_market_signals

    with SessionLocal() as db:
        count = ingest_market_signals(db)
        logger.info("Alpha Vantage job: %d new signals", count)


def _bls_job() -> None:
    """Fetch BLS primary-source labor and price indicators."""
    from backend.ingestion.bls import ingest_bls_indicators

    with SessionLocal() as db:
        count = ingest_bls_indicators(db)
        logger.info("BLS job: %d new indicators", count)


def _bea_job() -> None:
    """Fetch BEA national accounts data (GDP, PCE, corporate profits)."""
    from backend.ingestion.bea import ingest_bea_indicators

    with SessionLocal() as db:
        count = ingest_bea_indicators(db)
        logger.info("BEA job: %d new indicators", count)


def _world_bank_job() -> None:
    """Fetch World Bank cross-country macroeconomic indicators."""
    from backend.ingestion.world_bank import ingest_world_bank_indicators

    with SessionLocal() as db:
        count = ingest_world_bank_indicators(db)
        logger.info("World Bank job: %d new data points", count)


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

    # Alpha Vantage market signals every 30 minutes (conserves free-tier quota)
    _scheduler.add_job(_alpha_vantage_job, IntervalTrigger(minutes=30), id="alpha_vantage", replace_existing=True)

    # BLS primary data every 6 hours (data releases are infrequent)
    _scheduler.add_job(_bls_job, IntervalTrigger(hours=6), id="bls_poll", replace_existing=True)

    # BEA quarterly data daily (releases are monthly/quarterly)
    _scheduler.add_job(_bea_job, IntervalTrigger(hours=24), id="bea_poll", replace_existing=True)

    # World Bank annual data once per day
    _scheduler.add_job(_world_bank_job, IntervalTrigger(hours=24), id="world_bank_poll", replace_existing=True)

    _scheduler.start()
    _update_next_poll_time()
    logger.info(
        "Background scheduler started (RSS:30min, Market:15min, FRED:4h, "
        "AlphaVantage:30min, BLS:6h, BEA:24h, WorldBank:24h)"
    )
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
