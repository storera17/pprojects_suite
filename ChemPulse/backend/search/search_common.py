from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


def terms(query: str) -> list[str]:
    return [term for term in re.split(r"[^A-Za-z0-9+#@.-]+", query.lower()) if len(term) >= 2]


def json_words(value: str) -> str:
    try:
        parsed = json.loads(value or "[]")
        if isinstance(parsed, list):
            return " ".join(str(item) for item in parsed)
    except json.JSONDecodeError:
        pass
    return str(value or "")


def metadata(record_count: int, source: str, empty_state_reason: str | None = None) -> dict[str, Any]:
    return {
        "record_count": int(record_count),
        "source": source,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "empty_state_reason": "" if record_count else (empty_state_reason or "No local ChemPulse matches were found."),
    }


def items_response(items: list[dict[str, Any]], source: str, empty_state_reason: str | None = None) -> dict[str, Any]:
    return {"items": items, "metadata": metadata(len(items), source, empty_state_reason=empty_state_reason)}


def safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
