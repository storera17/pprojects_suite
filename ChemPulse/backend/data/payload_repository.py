from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.data.db import get_connection
from backend.data.schemas import CORE_INGESTION_SCHEMA_SQL

class PayloadRepository:
    @staticmethod
    def ensure_schema() -> None:
        with get_connection(read_only=False) as con:
            con.execute(CORE_INGESTION_SCHEMA_SQL)

    @staticmethod
    def save_payload(
        payload: dict[str, Any],
        *,
        source: str,
        status: str = "valid",
        record_count: int = 0,
        last_error: str = "",
        payload_id: str | None = None,
    ) -> dict[str, Any]:
        PayloadRepository.ensure_schema()
        now = datetime.now(timezone.utc)
        final_payload_id = payload_id or str(uuid.uuid4())
        existing = PayloadRepository.get_payload(final_payload_id)
        created_at = existing.get("created_at") if existing.get("available") else now
        with get_connection(read_only=False) as con:
            con.execute(
                """
                INSERT INTO chempulse_payloads (
                    payload_id, created_at, updated_at, source, status,
                    record_count, last_error, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(payload_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    source = excluded.source,
                    status = excluded.status,
                    record_count = excluded.record_count,
                    last_error = excluded.last_error,
                    payload_json = excluded.payload_json
                """,
                [
                    final_payload_id,
                    created_at,
                    now,
                    source,
                    status,
                    int(record_count),
                    _redact(last_error),
                    json.dumps(payload, ensure_ascii=True),
                ],
            )
        return PayloadRepository.get_payload(final_payload_id)

    @staticmethod
    def get_payload(payload_id: str) -> dict[str, Any]:
        PayloadRepository.ensure_schema()
        with get_connection(read_only=True) as con:
            row = con.execute(
                """
                SELECT payload_id, created_at, updated_at, source, status,
                       record_count, last_error, payload_json
                FROM chempulse_payloads
                WHERE payload_id = ?
                LIMIT 1
                """,
                [payload_id],
            ).fetchone()
        return _payload_record(row) if row else empty_payload()

    @staticmethod
    def latest_payload() -> dict[str, Any]:
        PayloadRepository.ensure_schema()
        with get_connection(read_only=True) as con:
            row = con.execute(
                """
                SELECT payload_id, created_at, updated_at, source, status,
                       record_count, last_error, payload_json
                FROM chempulse_payloads
                WHERE status = 'valid'
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ).fetchone()
        return _payload_record(row) if row else empty_payload()

def empty_payload() -> dict[str, Any]:
    return {
        "available": False,
        "payload_id": "",
        "created_at": "",
        "updated_at": "",
        "source": "",
        "status": "empty",
        "record_count": 0,
        "last_error": "",
        "payload": {},
        "message": "No previous ChemPulse payload has been saved yet.",
    }

def _payload_record(row: tuple[Any, ...]) -> dict[str, Any]:
    payload: dict[str, Any]
    try:
        payload = json.loads(row[7] or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "available": True,
        "payload_id": row[0],
        "created_at": _format_dt(row[1]),
        "updated_at": _format_dt(row[2]),
        "source": row[3],
        "status": row[4],
        "record_count": int(row[5] or 0),
        "last_error": _redact(str(row[6] or "")),
        "payload": payload,
        "message": "",
    }

def _format_dt(value: Any) -> str:
    if not value:
        return ""
    return value.isoformat() if hasattr(value, "isoformat") else str(value)

def _redact(message: str) -> str:
    redacted = re.sub(r"CORE_API_KEY\s*=\s*[^,\s;]+", "literature API key [redacted]", message or "")
    redacted = redacted.replace("CORE_API_KEY", "literature API key")
    redacted = re.sub(r"sk-[A-Za-z0-9_\-]+", "[redacted]", redacted)
    redacted = re.sub(r"LSl[A-Za-z0-9_\-]+", "[redacted]", redacted)
    return redacted
