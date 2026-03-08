"""Alpha Vantage market signals ingestion (free tier: 25 calls/day).

Fetches VIX, key equity indices, forex rates, and bond yield proxies —
the leading indicators the analysis engine references but previously couldn't source.

Free API key: https://www.alphavantage.co/support/#api-key
Set ALPHA_VANTAGE_API_KEY in .env to activate.
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

AV_SOURCE_NAME = "Alpha Vantage (Market Signals)"
AV_BASE_URL = "https://www.alphavantage.co/query"

# Symbols to fetch with their human descriptions and domains.
# Free tier allows ~25 calls/day; keep this list lean.
QUOTE_SYMBOLS: list[tuple[str, str]] = [
    ("SPY", "S&P 500 ETF — US equity market benchmark"),
    ("QQQ", "Nasdaq-100 ETF — technology sector proxy"),
    ("TLT", "20+ Year Treasury Bond ETF — long-duration interest rate signal"),
    ("GLD", "Gold ETF — safe-haven / inflation hedge signal"),
    ("USO", "Crude Oil ETF — energy market proxy"),
    ("EEM", "Emerging Markets ETF — EM risk appetite signal"),
    ("VXX", "VIX Short-Term Futures ETF — market volatility / fear gauge"),
    ("DXY", "US Dollar Index — USD strength signal"),
]

FOREX_PAIRS: list[tuple[str, str, str]] = [
    ("USD", "CNY", "USD/CNY — US-China trade tension proxy"),
    ("USD", "TWD", "USD/TWD — Taiwan financial stress indicator"),
    ("USD", "JPY", "USD/JPY — Asia risk-off signal"),
    ("EUR", "USD", "EUR/USD — transatlantic economic divergence"),
]


def _ensure_av_source(db: Session) -> Source:
    source = db.query(Source).filter(Source.name == AV_SOURCE_NAME).first()
    if not source:
        source = Source(
            name=AV_SOURCE_NAME,
            source_type="api",
            layer=6,
            bias_label="center",
            language="en",
            is_active=True,
            economic_school="empirical",
            economic_bias="center",
            salience_domains="markets",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def ingest_market_signals(db: Session) -> int:
    """Fetch Alpha Vantage market signals and store as ingested content.

    Args:
        db: SQLAlchemy session.

    Returns:
        Number of new signals ingested.
    """
    if not settings.alpha_vantage_api_key:
        logger.info("ALPHA_VANTAGE_API_KEY not set; skipping Alpha Vantage ingestion")
        return 0

    source = _ensure_av_source(db)
    new_count = 0
    now = datetime.now(UTC)

    with httpx.Client(timeout=15) as client:
        new_count += _ingest_quotes(client, source, db, now)
        new_count += _ingest_forex(client, source, db, now)

    db.commit()
    logger.info("Alpha Vantage: ingested %d new market signals", new_count)
    return new_count


def _ingest_quotes(client: httpx.Client, source: Source, db: Session, now: datetime) -> int:
    """Fetch global quote for each equity/ETF symbol."""
    count = 0
    for symbol, description in QUOTE_SYMBOLS:
        try:
            resp = client.get(
                AV_BASE_URL,
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": settings.alpha_vantage_api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json().get("Global Quote", {})
            if not data:
                logger.debug("Alpha Vantage: empty quote for %s", symbol)
                continue

            price = data.get("05. price", "N/A")
            change_pct = data.get("10. change percent", "N/A")
            latest_date = data.get("07. latest trading day", now.date().isoformat())

            title = f"Market Signal — {symbol}: ${price} ({change_pct}) as of {latest_date}"
            body = (
                f"Alpha Vantage market signal for {symbol} ({description}). "
                f"Price: ${price} | Change: {change_pct} | Date: {latest_date}. "
                f"Use as a leading indicator for financial market analysis. "
                f"Retrieved: {now.isoformat()}."
            )

            content_hash = compute_content_hash(title, body[:500])
            if is_duplicate(content_hash, db):
                continue

            doc_id = f"av_quote_{symbol}_{content_hash}"
            content = IngestedContent(
                source_id=source.id,
                content_hash=content_hash,
                url=f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}",
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
                    "source_name": AV_SOURCE_NAME,
                    "bias_label": "center",
                    "language": "en",
                    "layer": 6,
                    "economic_school": "empirical",
                    "economic_bias": "center",
                    "salience_domains": "markets",
                    "url": content.url,
                    "ingested_content_id": content.id,
                    "symbol": symbol,
                    "signal_type": "equity_quote",
                },
            )
            count += 1

        except Exception as exc:
            logger.warning("Alpha Vantage quote fetch failed for %s: %s", symbol, exc)

    return count


def _ingest_forex(client: httpx.Client, source: Source, db: Session, now: datetime) -> int:
    """Fetch real-time forex exchange rates."""
    count = 0
    for from_ccy, to_ccy, description in FOREX_PAIRS:
        try:
            resp = client.get(
                AV_BASE_URL,
                params={
                    "function": "CURRENCY_EXCHANGE_RATE",
                    "from_currency": from_ccy,
                    "to_currency": to_ccy,
                    "apikey": settings.alpha_vantage_api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json().get("Realtime Currency Exchange Rate", {})
            if not data:
                continue

            rate = data.get("5. Exchange Rate", "N/A")
            last_refreshed = data.get("6. Last Refreshed", now.isoformat())

            title = f"Forex Signal — {from_ccy}/{to_ccy}: {rate} as of {last_refreshed}"
            body = (
                f"Alpha Vantage forex signal: {description}. "
                f"Exchange rate {from_ccy}/{to_ccy}: {rate}. "
                f"Last refreshed: {last_refreshed}. "
                f"Use as a leading indicator for currency and trade analysis. "
                f"Retrieved: {now.isoformat()}."
            )

            content_hash = compute_content_hash(title, body[:500])
            if is_duplicate(content_hash, db):
                continue

            doc_id = f"av_fx_{from_ccy}{to_ccy}_{content_hash}"
            content = IngestedContent(
                source_id=source.id,
                content_hash=content_hash,
                url=f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_ccy}&to_currency={to_ccy}",
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
                    "source_name": AV_SOURCE_NAME,
                    "bias_label": "center",
                    "language": "en",
                    "layer": 6,
                    "economic_school": "empirical",
                    "economic_bias": "center",
                    "salience_domains": "markets",
                    "url": content.url,
                    "ingested_content_id": content.id,
                    "symbol": f"{from_ccy}/{to_ccy}",
                    "signal_type": "forex",
                },
            )
            count += 1

        except Exception as exc:
            logger.warning("Alpha Vantage forex fetch failed for %s/%s: %s", from_ccy, to_ccy, exc)

    return count
