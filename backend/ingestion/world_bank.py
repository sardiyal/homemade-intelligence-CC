"""World Bank Open Data ingestion — fully free, no API key required.

Fetches GDP growth, inflation, trade balance, and debt-to-GDP for key economies.
Provides the non-US international macroeconomic grounding that purely US-focused
sources miss — essential for balanced multi-school analysis.

API docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
"""

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session

from backend.database.models import IngestedContent, Source
from backend.ingestion.dedup import compute_content_hash, is_duplicate
from backend.vector_store.chroma import upsert_source_chunk

logger = logging.getLogger(__name__)

WB_SOURCE_NAME = "World Bank Open Data"
WB_BASE_URL = "https://api.worldbank.org/v2"

# (indicator_code, label, economic_interpretation)
WB_INDICATORS: list[tuple[str, str, str]] = [
    (
        "NY.GDP.MKTP.KD.ZG",
        "GDP Growth Rate (% annual)",
        "Cross-country output comparison. Tests convergence theory (neoclassical) vs. development traps (institutional/heterodox).",
    ),
    (
        "FP.CPI.TOTL.ZG",
        "CPI Inflation (% annual)",
        "International inflation comparison. Tests monetary transmission across different central bank regimes.",
    ),
    (
        "NE.TRD.GNFS.ZS",
        "Trade (% of GDP)",
        "Trade openness indicator. Neoclassical: comparative advantage; institutional: terms-of-trade power asymmetry.",
    ),
    (
        "GC.DOD.TOTL.GD.ZS",
        "Central Government Debt (% of GDP)",
        "Fiscal sustainability indicator. Keynesian: debt as demand tool; supply-side: crowding-out test; MMT: currency-issuer frame.",
    ),
    (
        "SL.UEM.TOTL.ZS",
        "Unemployment Rate (% total labor force)",
        "Cross-country unemployment. NAIRU comparison; structural vs. cyclical unemployment decomposition.",
    ),
]

# Countries to fetch: selected for geopolitical and economic relevance
WB_COUNTRIES: list[tuple[str, str]] = [
    ("US", "United States"),
    ("CN", "China"),
    ("TW", "Taiwan"),
    ("JP", "Japan"),
    ("DE", "Germany"),
    ("IN", "India"),
    ("GB", "United Kingdom"),
    ("EU", "Euro Area"),
    ("BR", "Brazil"),
    ("KR", "South Korea"),
]


def _ensure_wb_source(db: Session) -> Source:
    source = db.query(Source).filter(Source.name == WB_SOURCE_NAME).first()
    if not source:
        source = Source(
            name=WB_SOURCE_NAME,
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


def ingest_world_bank_indicators(db: Session) -> int:
    """Fetch World Bank indicators for key economies and store as ingested content.

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of new data points ingested.
    """
    source = _ensure_wb_source(db)
    new_count = 0
    now = datetime.now(UTC)
    current_year = now.year

    country_codes = ";".join(c[0] for c in WB_COUNTRIES)
    country_map = {c[0]: c[1] for c in WB_COUNTRIES}

    with httpx.Client(timeout=30) as client:
        for indicator_code, label, interpretation in WB_INDICATORS:
            try:
                resp = client.get(
                    f"{WB_BASE_URL}/country/{country_codes}/indicator/{indicator_code}",
                    params={
                        "format": "json",
                        "date": f"{current_year - 3}:{current_year}",
                        "per_page": "200",
                    },
                )
                resp.raise_for_status()
                payload = resp.json()

                if len(payload) < 2 or not payload[1]:
                    continue

                # Group by country, take most recent non-null value
                latest_by_country: dict[str, dict] = {}
                for obs in payload[1]:
                    country_id = obs.get("country", {}).get("id", "")
                    if obs.get("value") is None:
                        continue
                    if country_id not in latest_by_country:
                        latest_by_country[country_id] = obs

                for country_id, obs in latest_by_country.items():
                    country_name = country_map.get(country_id, obs.get("country", {}).get("value", country_id))
                    value = obs.get("value", "N/A")
                    date = obs.get("date", "")

                    value_str = f"{value:.2f}" if isinstance(value, float) else str(value)

                    title = f"World Bank — {country_name} {label}: {value_str}% ({date})"
                    body = (
                        f"World Bank Open Data: {label} for {country_name} ({country_id}). "
                        f"Value: {value_str} as of {date}. "
                        f"Economic interpretation: {interpretation} "
                        f"Source: World Bank national accounts / ILO data. "
                        f"Retrieved: {now.isoformat()}."
                    )

                    content_hash = compute_content_hash(title, body[:500])
                    if is_duplicate(content_hash, db):
                        continue

                    doc_id = f"wb_{indicator_code}_{country_id}_{content_hash}"
                    content = IngestedContent(
                        source_id=source.id,
                        content_hash=content_hash,
                        url=f"https://data.worldbank.org/indicator/{indicator_code}?locations={country_id}",
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
                            "source_name": WB_SOURCE_NAME,
                            "bias_label": "center",
                            "language": "en",
                            "layer": 3,
                            "economic_school": "empirical",
                            "economic_bias": "center",
                            "salience_domains": "markets,general",
                            "url": content.url,
                            "ingested_content_id": content.id,
                            "indicator": indicator_code,
                            "country": country_id,
                        },
                    )
                    new_count += 1

            except Exception as exc:
                logger.warning("World Bank indicator %s failed: %s", indicator_code, exc)

    db.commit()
    logger.info("World Bank: ingested %d new data points", new_count)
    return new_count
