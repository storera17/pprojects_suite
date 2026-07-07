from __future__ import annotations

from datetime import datetime, timezone

from backend.data.db import get_connection

TOPICS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chempulse_topics (
    term VARCHAR PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
"""
# Chemistry-focused defaults (mirror the publication agent's historical default query).
DEFAULT_TOPICS: list[str] = [
    "catalyst", "catalysis", "photocatalysis", "electrocatalysis", "organocatalysis",
    "molecular scaffold", "chemical scaffold", "medicinal chemistry", "heterocycle",
    "ligand", "cross-coupling", "reaction mechanism", "esterification",
]

# The chemistry-grounding clause keeps results on-topic regardless of the topic terms.
_GROUNDING_CLAUSE = "(chemistry OR synthesis OR reaction OR molecular OR compound)"

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)

def ensure_topics_schema() -> None:
    with get_connection(read_only=False) as con:
        con.execute(TOPICS_SCHEMA_SQL)

def seed_default_topics() -> int:
    """Insert the default topic set only if the registry is empty. Returns count seeded."""
    ensure_topics_schema()
    if list_topics():
        return 0
    set_topics(DEFAULT_TOPICS)
    return len(DEFAULT_TOPICS)

def list_topics() -> list[dict]:
    """All topics (for the dashboards), ordered."""
    ensure_topics_schema()
    with get_connection(read_only=True) as con:
        rows = con.execute(
            "SELECT term, enabled, sort_order FROM chempulse_topics ORDER BY sort_order, term"
        ).fetchall()
    return [{"term": r[0], "enabled": bool(r[1]), "sort_order": int(r[2])} for r in rows]

def active_topics() -> list[str]:
    """Enabled topic terms, in order — the input to the query compiler."""
    return [t["term"] for t in list_topics() if t["enabled"]]

def set_topics(terms: list[str]) -> list[dict]:
    """Replace the whole topic list (used when a dashboard saves the topic set)."""
    ensure_topics_schema()
    cleaned: list[str] = []
    seen: set[str] = set()
    for term in terms:
        t = (term or "").strip()
        if t and t.lower() not in seen:
            cleaned.append(t)
            seen.add(t.lower())
    now = _now()
    with get_connection(read_only=False) as con:
        con.execute("DELETE FROM chempulse_topics")
        for order, term in enumerate(cleaned):
            con.execute(
                "INSERT INTO chempulse_topics (term, enabled, sort_order, created_at, updated_at) "
                "VALUES (?, TRUE, ?, ?, ?)",
                [term, order, now, now],
            )
    return list_topics()

def set_enabled(term: str, enabled: bool) -> None:
    ensure_topics_schema()
    with get_connection(read_only=False) as con:
        con.execute(
            "UPDATE chempulse_topics SET enabled = ?, updated_at = ? WHERE term = ?",
            [bool(enabled), _now(), term],
        )

def _quote(term: str) -> str:
    """Quote multi-word terms for the CORE boolean query; leave single tokens bare."""
    term = term.strip()
    return f'"{term}"' if (" " in term or "-" in term) else term

def compile_core_query(terms: list[str]) -> str | None:
    """Compile enabled topic terms into a CORE boolean query with a `{year}` template.

    Returns ``None`` when there are no terms, so the caller falls back to the publication
    agent's configured default query instead of building an empty filter.

    Date filtering uses ``yearPublished>={year}``: CORE's current API rejects
    ``publishedDate``/``createdDate`` comparisons (Azure 'DateTimeOffset vs String' 500s),
    and only year-granular ``yearPublished`` filtering is accepted. ``{year}`` is
    substituted by CorePublicationAgent at run time; "search older publications" backfill is
    provided by the agent's offset paging through the result set.
    """
    cleaned = [t.strip() for t in terms if t and t.strip()]
    if not cleaned:
        return None
    topic_clause = " OR ".join(_quote(t) for t in cleaned)
    return f"(({topic_clause}) AND {_GROUNDING_CLAUSE} AND yearPublished>={{year}})"
