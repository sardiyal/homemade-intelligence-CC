"""BLS (Bureau of Labor Statistics) data ingestion — free public API.

Fetches CPI, PPI, unemployment, and nonfarm payrolls — primary-source
empirical data for economic theory grounding.

No API key required for basic access (up to 25 series/request, 10 years).
Optional BLS_API_KEY in .env allows 50 series and longer history.

API docs: https://www.bls.gov/developers/api_python.htm
"""

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.models import IngestedContent, Source
from backend.ingestion.dedup import compute_content_hash, is_duplicate
from backend.vector_store.chroma import upsert_source_chunk

logger = logging.getLogger(__name__)

BLS_SOURCE_NAME = "BLS (Bureau of Labor Statistics)"
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# BLS series IDs, labels, and economic interpretation
BLS_SERIES: list[tuple[str, str, str]] = [
    (
        "CUSR0000SA0",
        "CPI-U (All Urban Consumers, All Items, SA)",
        "Headline inflation — Keynesian demand-pull vs. monetarist money-supply pressure test",
    ),
    (
        "CUSR0000SA0L1E",
        "CPI-U ex Food & Energy (Core CPI, SA)",
        "Core inflation — strips supply shocks; key for Fed monetary policy decisions",
    ),
    (
        "WPU00000000",
        "PPI Final Demand (All Commodities)",
        "Producer price index — leading indicator for CPI; supply-side cost-push pressure",
    ),
    ("LNS14000000", "Unemployment Rate (U-3, SA)", "Headline unemployment — NAIRU proximity; Phillips Curve test"),
    ("LNS13000000", "Nonfarm Payrolls (level)", "Labor market strength — demand indicator for Fed dual mandate"),
    (
        "CES0500000003",
        "Average Hourly Earnings (Private, SA)",
        "Wage growth — wage-price spiral risk indicator; real wage vs. inflation gap",
    ),
]


def _ensure_bls_source(db: Session) -> Source:
    source = db.query(Source).filter(Source.name == BLS_SOURCE_NAME).first()
    if not source:
        source = Source(
            name=BLS_SOURCE_NAME,
            source_type="api",
            layer=3,
            bias_label="center",
            language="en",
            is_active=True,
            economic_school="empirical",
            economic_bias="center",
            salience_domains="markets,general",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def ingest_bls_indicators(db: Session) -> int:
    """Fetch latest BLS series values and store as ingested content.

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of new indicators ingested.
    """
    source = _ensure_bls_source(db)
    series_ids = [s[0] for s in BLS_SERIES]
    series_map = {s[0]: (s[1], s[2]) for s in BLS_SERIES}

    payload: dict = {
        "seriesid": series_ids,
        "startyear": str(datetime.now(UTC).year - 1),
        "endyear": str(datetime.now(UTC).year),
    }
    if settings.bls_api_key:
        payload["registrationkey"] = settings.bls_api_key

    new_count = 0
    now = datetime.now(UTC)

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.post(BLS_API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "REQUEST_SUCCEEDED":
            logger.warning("BLS API returned status: %s", data.get("status"))
            return 0

        for series in data.get("Results", {}).get("series", []):
            series_id = series.get("seriesID", "")
            label, interpretation = series_map.get(series_id, (series_id, ""))
            observations = series.get("data", [])
            if not observations:
                continue

            # Take only the most recent observation
            latest = observations[0]
            value = latest.get("value", "N/A")
            period_name = latest.get("periodName", "")
            year = latest.get("year", "")

            title = f"BLS {series_id}: {label} = {value} ({period_name} {year})"
            body = (
                f"BLS primary-source economic indicator: {label} (series {series_id}). "
                f"Latest value: {value} for {period_name} {year}. "
                f"Economic interpretation: {interpretation}. "
                f"Source: Bureau of Labor Statistics, US Department of Labor. "
                f"Retrieved: {now.isoformat()}."
            )

            content_hash = compute_content_hash(title, body[:500])
            if is_duplicate(content_hash, db):
                continue

            doc_id = f"bls_{series_id}_{content_hash}"
            content = IngestedContent(
                source_id=source.id,
                content_hash=content_hash,
                url=f"https://www.bls.gov/timeseries/{series_id}",
                title=title,
                body=body,
                published_at=now,
                is_manual=False,
                chroma_doc_id=doc_id,
            )
            db.add(content)
            db.flush()

            upsert_source_chunk(
                doc_id=doc_id,
                text=f"{title}\n\n{body}",
                metadata={
                    "source_id": source.id,
                    "source_name": BLS_SOURCE_NAME,
                    "bias_label": "center",
                    "language": "en",
                    "layer": 3,
                    "economic_school": "empirical",
                    "economic_bias": "center",
                    "salience_domains": "markets,general",
                    "url": content.url,
                    "ingested_content_id": content.id,
                    "series_id": series_id,
                },
            )
            new_count += 1

    except Exception as exc:
        logger.warning("BLS ingestion failed: %s", exc)

    db.commit()
    logger.info("BLS: ingested %d new indicator values", new_count)
    return new_count
