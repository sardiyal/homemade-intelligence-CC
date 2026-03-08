"""ChromaDB client with two collections: sources and reports."""

import logging
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb import Collection

from backend.config import settings

logger = logging.getLogger(__name__)

SOURCES_COLLECTION = "sources"
REPORTS_COLLECTION = "reports"


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client (singleton)."""
    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    logger.info("ChromaDB client initialized at %s", persist_dir)
    return client


def get_sources_collection() -> Collection:
    """Return the sources collection, creating if it doesn't exist."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=SOURCES_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def get_reports_collection() -> Collection:
    """Return the reports collection, creating if it doesn't exist."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=REPORTS_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_source_chunk(
    doc_id: str,
    text: str,
    metadata: dict,
) -> None:
    """Upsert a single content chunk into the sources collection."""
    col = get_sources_collection()
    col.upsert(ids=[doc_id], documents=[text], metadatas=[metadata])


def upsert_report_summary(
    doc_id: str,
    text: str,
    metadata: dict,
) -> None:
    """Upsert a report summary into the reports collection."""
    col = get_reports_collection()
    col.upsert(ids=[doc_id], documents=[text], metadatas=[metadata])


def query_sources(query_text: str, n_results: int = 15) -> list[dict]:
    """Semantic search over the sources collection.

    Returns:
        List of dicts with keys: id, document, metadata, distance.
    """
    col = get_sources_collection()
    count = col.count()
    if count == 0:
        return []
    n_results = min(n_results, count)
    results = col.query(query_texts=[query_text], n_results=n_results)
    return _flatten_results(results)


def query_sources_with_salience(
    query_text: str,
    domain: str,
    n_results: int = 15,
    salience_boost: float = 0.08,
) -> list[dict]:
    """Semantic search with topic-conditioned salience re-ranking (Decision 3B — Option C).

    Fetches an oversample (2x n_results) from ChromaDB, applies a salience boost to
    sources whose salience_domains metadata matches the requested domain, then
    re-ranks and returns the top n_results.

    The boost reduces the cosine distance (lower = more similar) for domain-matching
    sources, effectively promoting them in the final ranking without excluding others.

    Args:
        query_text: The semantic query string.
        domain: Report domain (e.g. 'markets', 'energy', 'taiwan', 'geopolitics').
        n_results: Final number of results to return after re-ranking.
        salience_boost: Distance reduction applied to domain-matching sources (default 0.08).

    Returns:
        List of dicts with keys: id, document, metadata, distance, salience_boosted.
    """
    col = get_sources_collection()
    count = col.count()
    if count == 0:
        return []

    # Oversample so re-ranking has material to work with
    fetch_n = min(n_results * 2, count)
    results = col.query(query_texts=[query_text], n_results=fetch_n)
    flat = _flatten_results(results)

    # Apply salience boost: reduce distance for domain-matching sources
    domain_lower = (domain or "").lower()
    for item in flat:
        salience_raw = item.get("metadata", {}).get("salience_domains", "") or ""
        source_domains = {d.strip().lower() for d in salience_raw.split(",") if d.strip()}
        boosted = domain_lower in source_domains
        if boosted:
            item["distance"] = max(0.0, item["distance"] - salience_boost)
        item["salience_boosted"] = boosted

    # Re-rank by adjusted distance (ascending — lower = better match)
    flat.sort(key=lambda x: x["distance"])
    return flat[:n_results]


def query_reports(query_text: str, n_results: int = 3) -> list[dict]:
    """Semantic search over the reports collection.

    Returns:
        List of dicts with keys: id, document, metadata, distance.
    """
    col = get_reports_collection()
    count = col.count()
    if count == 0:
        return []
    n_results = min(n_results, count)
    results = col.query(query_texts=[query_text], n_results=n_results)
    return _flatten_results(results)


def _flatten_results(results: dict) -> list[dict]:
    """Flatten ChromaDB query result structure into a list of dicts."""
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    return [
        {"id": i, "document": d, "metadata": m, "distance": dist}
        for i, d, m, dist in zip(ids, docs, metas, dists, strict=False)
    ]
