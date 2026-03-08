"""BEA (Bureau of Economic Analysis) data ingestion — free public API.

Fetches GDP, PCE, personal income, and corporate profits — primary-source
data essential for cross-school economic theory comparison.

Free API key required: https://apps.bea.gov/api/signup/
Set BEA_API_KEY in .env to activate.

API docs: https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf
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

BEA_SOURCE_NAME = "BEA (Bureau of Economic Analysis)"
BEA_BASE_URL = "https://apps.bea.gov/api/data"

# BEA NIPA table / line / description / economic interpretation
BEA_NIPA_SERIES: list[dict] = [
    {
        "TableName": "T10101",
        "LineNumber": "1",
        "label": "Real GDP (% change, annualized)",
        "interpretation": (
            "Primary output measure. Keynesian: demand shortfall test. "
            "Supply-side: productivity and incentive effects test. "
            "Monetarist: nominal GDP decomposition (RGDP + inflation)."
        ),
    },
    {
        "TableName": "T20305",
        "LineNumber": "1",
        "label": "PCE Price Index (% change) — Fed's preferred inflation gauge",
        "interpretation": (
            "Personal Consumption Expenditures deflator. "
            "Preferred by the Fed over CPI. Key for monetarist and Keynesian framework comparison."
        ),
    },
    {
        "TableName": "T20100",
        "LineNumber": "1",
        "label": "Personal Income ($ billions, SAAR)",
        "interpretation": (
            "Income side of GDP. "
            "Keynesian: consumption function driver. "
            "Supply-side: wage and incentive structure indicator."
        ),
    },
    {
        "TableName": "T61500",
        "LineNumber": "1",
        "label": "Corporate Profits Before Tax ($ billions, SAAR)",
        "interpretation": (
            "Corporate profit share of national income. "
            "Institutional: labor vs. capital income distribution test. "
            "Supply-side: investment incentive indicator."
        ),
    },
]


def _ensure_bea_source(db: Session) -> Source:
    source = db.query(Source).filter(Source.name == BEA_SOURCE_NAME).first()
    if not source:
        source = Source(
            name=BEA_SOURCE_NAME,
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


def ingest_bea_indicators(db: Session) -> int:
    """Fetch latest BEA NIPA series and store as ingested content.

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of new indicators ingested.
    """
    if not settings.bea_api_key:
        logger.info("BEA_API_KEY not set; skipping BEA ingestion")
        return 0

    source = _ensure_bea_source(db)
    new_count = 0
    now = datetime.now(UTC)
    current_year = now.year

    with httpx.Client(timeout=20) as client:
        for series in BEA_NIPA_SERIES:
            try:
                params = {
                    "UserID": settings.bea_api_key,
                    "method": "GetData",
                    "datasetname": "NIPA",
                    "TableName": series["TableName"],
                    "Frequency": "Q",
                    "Year": f"{current_year - 1},{current_year}",
                    "ResultFormat": "JSON",
                }
                resp = client.get(BEA_BASE_URL, params=params)
                resp.raise_for_status()
                payload = resp.json()

                results = payload.get("BEAAPI", {}).get("Results", {}).get("Data", [])
                # Filter to matching line number
                line_no = series["LineNumber"]
                matching = [r for r in results if str(r.get("LineNumber", "")) == line_no]
                if not matching:
                    continue

                # Most recent observation (last in list)
                latest = matching[-1]
                value = latest.get("DataValue", "N/A")
                time_period = latest.get("TimePeriod", "")

                label = series["label"]
                title = f"BEA {series['TableName']} L{line_no}: {label} = {value} ({time_period})"
                body = (
                    f"BEA primary-source national accounts data: {label}. "
                    f"Latest value: {value} for {time_period}. "
                    f"Economic interpretation: {series['interpretation']} "
                    f"Source: Bureau of Economic Analysis, US Department of Commerce. "
                    f"Retrieved: {now.isoformat()}."
                )

                content_hash = compute_content_hash(title, body[:500])
                if is_duplicate(content_hash, db):
                    continue

                doc_id = f"bea_{series['TableName']}_L{line_no}_{content_hash}"
                content = IngestedContent(
                    source_id=source.id,
                    content_hash=content_hash,
                    url="https://apps.bea.gov/itable/",
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
                        "source_name": BEA_SOURCE_NAME,
                        "bias_label": "center",
                        "language": "en",
                        "layer": 3,
                        "economic_school": "empirical",
                        "economic_bias": "center",
                        "salience_domains": "markets,general",
                        "url": content.url,
                        "ingested_content_id": content.id,
                        "series_id": f"{series['TableName']}_L{line_no}",
                    },
                )
                new_count += 1

            except Exception as exc:
                logger.warning("BEA series %s L%s failed: %s", series["TableName"], series["LineNumber"], exc)

    db.commit()
    logger.info("BEA: ingested %d new indicator values", new_count)
    return new_count
