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