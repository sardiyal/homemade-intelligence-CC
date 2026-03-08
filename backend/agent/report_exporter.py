"""Export Report records to markdown files in reports/{en,zh-tw,zh-tw-elder}/."""

import logging
import re
from pathlib import Path

from backend.database.models import Report
from backend.vector_store.chroma import upsert_report_summary

logger = logging.getLogger(__name__)


def embed_report_summary(report: Report) -> None:
    """Embed a report's English summary into ChromaDB for semantic retrieval.

    Safe to call after DB commit — sets report.chroma_doc_id in memory.
    No-op if report has no English content.

    Args:
        report: Completed Report ORM object.
    """
    if not report.content_en:
        return
    try:
        doc_id = f"report_{report.id}"
        upsert_report_summary(
            doc_id=doc_id,
            text=report.content_en[:800],
            metadata={
                "report_id": report.id,
                "topic": report.topic,
                "domain": report.domain or "",
                "created_at": report.created_at.isoformat() if report.created_at else "",
                "bias_score": report.bias_score or 0.0,
            },
        )
        report.chroma_doc_id = doc_id
    except Exception as exc:
        logger.warning("ChromaDB report embedding failed: %s", exc)


REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"

_AUDIENCE_DIRS = {
    "en": "en",
    "zh_tw": "zh-tw",
    "zh_tw_elder": "zh-tw-elder",
}


def _slugify(topic: str) -> str:
    """Convert a topic string to a filename-safe slug."""
    slug = topic.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def _build_frontmatter(report: Report, audience: str) -> str:
    """Build YAML frontmatter for a report markdown file."""
    date_str = report.created_at.strftime("%Y-%m-%d") if report.created_at else "unknown"
    lines = [
        "---",
        f"date: {date_str}",
        f'audience: "{audience}"',
        f'topic: "{_slugify(report.topic)}"',
        f'domain: "{report.domain or "general"}"',
    ]
    if report.bias_score is not None:
        lines.append(f"bias_score: {report.bias_score:.2f}")
    if report.cost_usd is not None:
        lines.append(f"cost_usd: {report.cost_usd:.4f}")
    lines.append("---")
    return "\n".join(lines)


def export_report_to_markdown(report: Report) -> list[Path]:
    """Export a single report's 3 audience versions to markdown files.

    Creates files like: reports/en/2026-03-07-top-10-intelligence-briefing.md

    Args:
        report: Report ORM object with content_en, content_zh_tw, content_zh_tw_elder.

    Returns:
        List of paths that were written.
    """
    if not report.created_at:
        logger.warning("Report %d has no created_at, skipping export", report.id)
        return []

    date_prefix = report.created_at.strftime("%Y-%m-%d")
    slug = _slugify(report.topic)
    filename = f"{date_prefix}-{slug}.md"

    content_map = {
        "en": report.content_en,
        "zh_tw": report.content_zh_tw,
        "zh_tw_elder": report.content_zh_tw_elder,
    }

    written: list[Path] = []

    for audience_key, content in content_map.items():
        if not content:
            continue

        dir_name = _AUDIENCE_DIRS[audience_key]
        out_dir = REPORTS_DIR / dir_name
        out_dir.mkdir(parents=True, exist_ok=True)

        frontmatter = _build_frontmatter(report, audience_key.replace("_", "-"))
        full_content = f"{frontmatter}\n\n{content}\n"

        out_path = out_dir / filename
        out_path.write_text(full_content, encoding="utf-8")
        written.append(out_path)
        logger.info("Exported report %d (%s) -> %s", report.id, audience_key, out_path)

    return written


def export_all_reports() -> int:
    """Export all completed reports from the database to markdown files.

    Returns:
        Number of reports exported.
    """
    from backend.database.connection import SessionLocal

    with SessionLocal() as db:
        reports = db.query(Report).filter(Report.status == "complete").order_by(Report.created_at).all()

        count = 0
        for report in reports:
            paths = export_report_to_markdown(report)
            if paths:
                count += 1

    logger.info("Bulk export complete: %d reports exported", count)
    return count
