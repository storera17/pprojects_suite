from __future__ import annotations

import json
from typing import Any

from app.db.connection import connect, fetchall_with_schema, json_dumps, utc_now


def set_provider_status(provider: str, status: str, message: str | None = None, raw_json: Any | None = None) -> None:
    now = utc_now()
    with connect() as conn:
        old = conn.execute("SELECT last_success_at FROM provider_status WHERE provider = ?", (provider,)).fetchone()
        last_success = now if status == "ok" else (old["last_success_at"] if old else None)
        conn.execute(
            """
            INSERT INTO provider_status(provider, status, message, last_success_at, last_attempt_at, raw_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                status=excluded.status,
                message=excluded.message,
                last_success_at=excluded.last_success_at,
                last_attempt_at=excluded.last_attempt_at,
                raw_json=excluded.raw_json
            """,
            (provider, status, message, last_success, now, json_dumps(raw_json) if raw_json is not None else None),
        )


def get_provider_statuses() -> list[dict[str, Any]]:
    rows = fetchall_with_schema("SELECT * FROM provider_status ORDER BY provider")
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            raw = json.loads(item.get("raw_json") or "{}")
        except Exception:
            raw = {}
        if isinstance(raw, dict):
            item["source"] = raw.get("source")
            item["cache_source"] = raw.get("cache_source") or raw.get("source")
            item["rate_limit_fallback"] = bool(raw.get("rate_limit_fallback"))
            item["fallback_active"] = bool(raw.get("fallback_active"))
            item["fallback_reason"] = raw.get("degraded_reason") or raw.get("provider_error_status")
            item["provider_error_status"] = raw.get("provider_error_status")
            item["provider_error_message"] = raw.get("provider_error_message")
            item["cache_record_count"] = raw.get("cache_record_count")
            item["cache_ttl_seconds"] = raw.get("cache_ttl_seconds")
            item["cache_age_seconds"] = raw.get("cache_age_seconds")
            item["cache_age_minutes"] = raw.get("cache_age_minutes")
            item["cache_fresh"] = raw.get("cache_fresh")
            item["cache_collected_at"] = raw.get("cache_collected_at") or item.get("last_success_at")
        output.append(item)
    return output
