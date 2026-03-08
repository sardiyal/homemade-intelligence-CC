"""Identifies the most important recent topics from ingested content using Claude."""

import json
import logging
from datetime import UTC, datetime, timedelta

import anthropic

from backend.config import settings
from backend.schemas.batch import IdentifiedTopic

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an intelligence analyst tasked with identifying the most important and newsworthy topics from a feed of recently ingested news articles.

Your goal is to surface distinct, high-priority topics that warrant in-depth intelligence analysis. Prioritize topics with significant developments in the last 48 hours, but also consider major ongoing situations from the past 7 days.

Rules:
- Each topic must be distinct — no near-duplicates
- Topics should span diverse domains (geopolitics, markets, taiwan, energy, general)
- Each topic string should be a clear, specific analysis question (10-80 words)
- Domain must be exactly one of: geopolitics, markets, taiwan, energy, general
- Return valid JSON only — no markdown fences, no prose"""

_USER_TEMPLATE = """Analyze the following {count} recent news articles (sorted newest first) and identify the {max_topics} most important topics for in-depth intelligence analysis.

Prioritize topics with significant developments in the last 48 hours (articles marked with [RECENT]).
Ensure domain diversity across geopolitics, markets, taiwan, energy, and general.

Articles:
{articles}

Return a JSON array of exactly {max_topics} objects with this schema:
[
  {{
    "topic": "Specific analysis question or topic description (10-80 words)",
    "domain": "geopolitics|markets|taiwan|energy|general",
    "rationale": "One sentence explaining why this is important right now"
  }},
  ...
]"""


async def identify_top_topics(days_lookback: int = 7, max_topics: int = 10) -> list[IdentifiedTopic]:
    """Identify the most important recent topics from ingested content.

    Queries the last N days of non-manual ingested content, sends titles and
    snippets to Claude, and returns a ranked list of analysis topics.

    Args:
        days_lookback: How many days of content to scan.
        max_topics: How many topics to identify.

    Returns:
        List of IdentifiedTopic objects, ranked by importance.
    """
    from backend.database.connection import SessionLocal
    from backend.database.models import IngestedContent

    cutoff = datetime.now(UTC) - timedelta(days=days_lookback)
    recent_cutoff = datetime.now(UTC) - timedelta(hours=48)

    with SessionLocal() as db:
        rows = (
            db.query(IngestedContent)
            .filter(
                IngestedContent.is_manual == False,  # noqa: E712
                IngestedContent.ingested_at >= cutoff,
            )
            .order_by(IngestedContent.ingested_at.desc())
            .limit(200)
            .all()
        )

    if not rows:
        logger.warning("No ingested content found in the last %d days", days_lookback)
        return []

    article_lines: list[str] = []
    for row in rows:
        is_recent = row.ingested_at and row.ingested_at.replace(tzinfo=UTC) >= recent_cutoff
        tag = "[RECENT] " if is_recent else ""
        title = (row.title or "").strip()
        snippet = (row.body or "")[:200].strip().replace("\n", " ")
        ingested = row.ingested_at.strftime("%Y-%m-%d %H:%M") if row.ingested_at else ""
        article_lines.append(f"{tag}[{ingested}] {title} — {snippet}")

    articles_text = "\n".join(article_lines)
    user_message = _USER_TEMPLATE.format(
        count=len(rows),
        max_topics=max_topics,
        articles=articles_text,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON array if there's surrounding text
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                parsed = json.loads(raw[start:end])
            except json.JSONDecodeError:
                logger.error("Topic identifier: Claude returned non-JSON: %s", raw[:200])
                return []
        else:
            logger.error("Topic identifier: Claude returned non-JSON: %s", raw[:200])
            return []

    topics: list[IdentifiedTopic] = []
    valid_domains = {"geopolitics", "markets", "taiwan", "energy", "general"}
    for item in parsed[:max_topics]:
        try:
            domain = item.get("domain", "general")
            if domain not in valid_domains:
                domain = "general"
            topics.append(
                IdentifiedTopic(
                    topic=item["topic"],
                    domain=domain,
                    rationale=item.get("rationale", ""),
                )
            )
        except (KeyError, TypeError) as exc:
            logger.warning("Skipping malformed topic entry: %s — %s", item, exc)

    logger.info("Topic identifier: found %d topics from %d articles", len(topics), len(rows))
    return topics
