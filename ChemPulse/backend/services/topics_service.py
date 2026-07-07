from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.data import topics_repository
from backend.core.paths import storage_dir

MAX_TERM_LENGTH = 120
MAX_TOPICS = 200
# Characters that would break the CORE boolean query the compiler builds.
_FORBIDDEN_CHARS = ('(', ')', '"')
_WHITESPACE = re.compile(r"\s+")


# --- normalization + validation ---------------------------------------------

def normalize_term(term: Any) -> str:
    """Trim + collapse internal whitespace. Idempotent."""
    return _WHITESPACE.sub(" ", str(term if term is not None else "").strip())


def validate_term(term: Any) -> str | None:
    """Return an error message for an invalid term, or None if it's acceptable."""
    t = normalize_term(term)
    if not t:
        return "empty topic"
    if len(t) > MAX_TERM_LENGTH:
        return f"topic too long (> {MAX_TERM_LENGTH} chars)"
    if any(ch in t for ch in _FORBIDDEN_CHARS):
        return "topic may not contain parentheses or double quotes"
    return None


def validate_topics(terms: list[Any]) -> tuple[list[str], list[str]]:
    """Normalize + validate + de-duplicate (case-insensitive). Returns (clean, errors)."""
    clean: list[str] = []
    errors: list[str] = []
    seen: set[str] = set()
    for term in terms or []:
        error = validate_term(term)
        if error:
            errors.append(f"{term!r}: {error}")
            continue
        norm = normalize_term(term)
        key = norm.lower()
        if key in seen:
            continue
        seen.add(key)
        clean.append(norm)
    if len(clean) > MAX_TOPICS:
        errors.append(f"too many topics ({len(clean)} > {MAX_TOPICS}); extra dropped")
        clean = clean[:MAX_TOPICS]
    return clean, errors


def normalize_terms(terms: list[Any]) -> list[str]:
    """Normalized, de-duplicated terms (drops invalid ones) — used before handing topics to
    CorePublicationAgent so the query is always built from clean terms."""
    clean, _ = validate_topics(terms)
    return clean


# --- reads -------------------------------------------------------------------

def list_topics() -> list[dict]:
    return topics_repository.list_topics()


def active_terms() -> list[str]:
    """Normalized, enabled topic terms — the authoritative input to the query compiler."""
    return normalize_terms(topics_repository.active_topics())


def compile_query() -> str | None:
    return topics_repository.compile_core_query(active_terms())


def ensure_seeded() -> int:
    """Seed the default chemistry topics if the store is empty. Returns count seeded."""
    return topics_repository.seed_default_topics()


# --- writes (validated + normalized → DuckDB) -------------------------------

def set_topics(terms: list[Any]) -> dict:
    """Replace the topic set. Validates + normalizes, persists the clean set to DuckDB,
    and reports any rejected terms. Never raises on bad input — returns errors instead."""
    clean, errors = validate_topics(terms)
    topics_repository.set_topics(clean)
    return {"ok": not errors, "topics": list_topics(), "errors": errors}


def add_topic(term: Any) -> dict:
    error = validate_term(term)
    if error:
        return {"ok": False, "topics": list_topics(), "errors": [f"{term!r}: {error}"]}
    current = [t["term"] for t in topics_repository.list_topics()]
    return set_topics(current + [normalize_term(term)])


def set_enabled(term: Any, enabled: bool) -> dict:
    topics_repository.set_enabled(normalize_term(term), bool(enabled))
    return {"ok": True, "topics": list_topics(), "errors": []}


def update_from_command_center(payload: dict) -> dict:
    """Safe update entry point for the Command Center registry bridge.

    Accepts ``{"topics": [...]}`` (full replace) and/or ``{"enable": {term: bool}}``.
    Always validates/normalizes; persists to DuckDB; returns ``{ok, topics, errors}``.
    """
    if not isinstance(payload, dict):
        return {"ok": False, "topics": list_topics(), "errors": ["payload must be an object"]}
    errors: list[str] = []
    if "topics" in payload:
        result = set_topics(payload.get("topics") or [])
        errors.extend(result["errors"])
    for term, enabled in (payload.get("enable") or {}).items():
        set_enabled(term, bool(enabled))
    return {"ok": not errors, "topics": list_topics(), "errors": errors}


# --- optional YAML export / import / backup / seeding -----------------------

def _require_yaml():
    try:
        import yaml  # noqa: PLC0415 — optional dependency, imported lazily
        return yaml
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on env
        raise RuntimeError(
            "YAML support is optional and requires PyYAML (pip install pyyaml). "
            "DuckDB remains the authoritative topic store."
        ) from exc


def default_yaml_path() -> Path:
    return storage_dir() / "publication_topics.yaml"


def export_to_yaml(path: str | Path | None = None) -> Path:
    """Export the current topics to a YAML file (export/backup). DuckDB stays authoritative."""
    yaml = _require_yaml()
    target = Path(path) if path else default_yaml_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump({"topics": list_topics(),
                        "exported_at": datetime.now(tz=timezone.utc).isoformat()},
                       sort_keys=False, allow_unicode=True),
        encoding="utf-8")
    return target


def backup_to_yaml() -> Path:
    """Write a timestamped YAML backup under storage/backups/."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
    return export_to_yaml(storage_dir() / "backups" / f"publication_topics-{ts}.yaml")


def import_from_yaml(path: str | Path) -> dict:
    """Import topics from a YAML file into DuckDB (import/seed). Validated + normalized."""
    yaml = _require_yaml()
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    raw = data.get("topics", data) if isinstance(data, dict) else data
    terms: list[Any] = []
    enable: dict[str, bool] = {}
    for entry in raw or []:
        if isinstance(entry, dict):
            term = entry.get("term")
            if term:
                terms.append(term)
                enable[normalize_term(term)] = bool(entry.get("enabled", True))
        else:
            terms.append(entry)
    result = set_topics(terms)
    for term, enabled in enable.items():
        if not enabled:
            topics_repository.set_enabled(term, False)
    result["topics"] = list_topics()
    return result
