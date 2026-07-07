from __future__ import annotations

from typing import Any

from backend.data.core_publication_repository import ensure_core_ingestion_schema
from backend.data.db import query_records

COMPLETED_STATUSES = {"succeeded", "insufficient"}
FAILED_STATUSES = {"failed"}
PRODUCTION_TARGET_RUNS = 7  # consecutive successful scheduled runs required for Production


def _fmt(row: dict | None) -> dict | None:
    if not row:
        return None
    return {
        "at": str(row.get("finished_at") or row.get("started_at") or ""),
        "status": row.get("status"),
        "inserted": int(row.get("inserted_count") or 0),
        "error": row.get("error_message") or "",
    }


class RunHealthService:
    @staticmethod
    def summary() -> dict[str, Any]:
        ensure_core_ingestion_schema()
        rows = query_records(
            "SELECT status, started_at, finished_at, inserted_count, error_message "
            "FROM core_ingestion_runs WHERE status != 'running' ORDER BY started_at DESC"
        )

        consecutive_successful = 0
        for r in rows:
            if r["status"] in COMPLETED_STATUSES:
                consecutive_successful += 1
            else:
                break

        consecutive_failed = 0
        for r in rows:
            if r["status"] in FAILED_STATUSES:
                consecutive_failed += 1
            else:
                break

        last_successful = next((r for r in rows if r["status"] in COMPLETED_STATUSES), None)
        last_failed = next((r for r in rows if r["status"] in FAILED_STATUSES), None)

        if not rows:
            health = "unknown"
        elif rows[0]["status"] in FAILED_STATUSES:
            health = "failing"
        else:
            health = "healthy"

        return {
            "health": health,
            "consecutive_successful_runs": consecutive_successful,
            "consecutive_failed_runs": consecutive_failed,
            "last_successful_run": _fmt(last_successful),
            "last_failed_run": _fmt(last_failed),
            "total_runs": len(rows),
            # Beta -> Production Ready progress (the measurable criterion).
            "production_target_runs": PRODUCTION_TARGET_RUNS,
            "production_ready_runs_met": consecutive_successful >= PRODUCTION_TARGET_RUNS,
            "production_progress": f"{min(consecutive_successful, PRODUCTION_TARGET_RUNS)}/{PRODUCTION_TARGET_RUNS}",
        }
