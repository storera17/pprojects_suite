from __future__ import annotations

import json
from typing import Any

from app.core.errors import AutoAgentRunBusyError
from app.db.connection import connect, fetchall_with_schema, json_dumps, utc_now
from app.db.schema import AUTO_AGENT_LOCK_NAME


def start_refresh_run(tickers: list[str], message: str = "manual refresh started") -> int:
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO refresh_runs(started_at, status, tickers, message) VALUES (?, ?, ?, ?)",
            (utc_now(), "running", ",".join(tickers), message),
        )
        return int(cursor.lastrowid)


def finish_refresh_run(run_id: int, status: str, message: str, raw_json: Any | None = None) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE refresh_runs SET finished_at=?, status=?, message=?, raw_json=? WHERE id=?",
            (utc_now(), status, message, json.dumps(raw_json, default=str)[:50000] if raw_json is not None else None, run_id),
        )


def _row_to_auto_agent_run(row) -> dict[str, Any] | None:
    if not row:
        return None
    item = dict(row)
    try:
        item["raw"] = json.loads(item.get("raw_json") or "{}")
    except Exception:
        item["raw"] = {}
    return item


def _ensure_auto_agent_state_row(conn) -> None:
    conn.execute(
        """
        INSERT INTO auto_agent_state(lock_name, active_run_id, mode, tickers, claimed_at, heartbeat_at, message)
        VALUES (?, NULL, NULL, NULL, NULL, NULL, NULL)
        ON CONFLICT(lock_name) DO NOTHING
        """,
        (AUTO_AGENT_LOCK_NAME,),
    )


def _clear_auto_agent_lock(conn) -> None:
    conn.execute(
        """
        UPDATE auto_agent_state
        SET active_run_id=NULL, mode=NULL, tickers=NULL, claimed_at=NULL, heartbeat_at=NULL, message=NULL
        WHERE lock_name=?
        """,
        (AUTO_AGENT_LOCK_NAME,),
    )


def reconcile_stale_auto_agent_runs(reason: str = "startup_recovery") -> list[dict[str, Any]]:
    recovered_at = utc_now()
    message = "Recovered orphaned auto agent run after restart."
    if reason and reason != "startup_recovery":
        message = f"Recovered orphaned auto agent run ({reason})."

    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _ensure_auto_agent_state_row(conn)
        rows = conn.execute(
            """
            SELECT * FROM auto_agent_runs
            WHERE status = 'running'
            ORDER BY started_at ASC, id ASC
            """
        ).fetchall()
        reconciled: list[dict[str, Any]] = []
        for row in rows:
            run = _row_to_auto_agent_run(row) or {}
            raw = dict(run.get("raw") or {})
            raw["reconciled"] = True
            raw["reconciled_at"] = recovered_at
            raw["reconciled_reason"] = reason
            conn.execute(
                """
                UPDATE auto_agent_runs
                SET finished_at=?, status=?, message=?, raw_json=?
                WHERE id=?
                """,
                (
                    recovered_at,
                    "error",
                    f"{message} Previous process stopped before the run could finish.",
                    json_dumps(raw)[:50000],
                    int(run["id"]),
                ),
            )
            run["finished_at"] = recovered_at
            run["status"] = "error"
            run["message"] = f"{message} Previous process stopped before the run could finish."
            run["raw"] = raw
            reconciled.append(run)
        _clear_auto_agent_lock(conn)
        return reconciled


def start_auto_agent_run(mode: str, tickers: list[str] | None = None, message: str | None = None) -> int:
    now = utc_now()
    tickers_csv = ",".join(tickers or [])
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _ensure_auto_agent_state_row(conn)
        state = conn.execute(
            """
            SELECT active_run_id, claimed_at, heartbeat_at, mode, tickers, message
            FROM auto_agent_state
            WHERE lock_name = ?
            """,
            (AUTO_AGENT_LOCK_NAME,),
        ).fetchone()
        active_run_id = int(state["active_run_id"]) if state and state["active_run_id"] is not None else None
        if active_run_id is not None:
            active_run_row = conn.execute("SELECT * FROM auto_agent_runs WHERE id = ?", (active_run_id,)).fetchone()
            active_run = _row_to_auto_agent_run(active_run_row)
            if active_run and active_run.get("status") == "running":
                raise AutoAgentRunBusyError(
                    active_run=active_run,
                    message=f"Another auto agent run is already active (run {active_run['id']}).",
                )
            _clear_auto_agent_lock(conn)

        cursor = conn.execute(
            """
            INSERT INTO auto_agent_runs(started_at, status, mode, tickers, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (now, "running", mode, tickers_csv, message or "auto cached agent run started"),
        )
        run_id = int(cursor.lastrowid)
        conn.execute(
            """
            UPDATE auto_agent_state
            SET active_run_id=?, mode=?, tickers=?, claimed_at=?, heartbeat_at=?, message=?
            WHERE lock_name=?
            """,
            (run_id, mode, tickers_csv, now, now, message or "auto cached agent run started", AUTO_AGENT_LOCK_NAME),
        )
        return run_id


def finish_auto_agent_run(
    run_id: int,
    status: str,
    result: dict[str, Any] | None = None,
    message: str | None = None,
) -> None:
    payload = result or {}
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            UPDATE auto_agent_runs
            SET finished_at=?, status=?, stale_categories=?, refreshed_tickers=?, provider_calls_skipped=?,
                fallbacks_used=?, message=?, raw_json=?
            WHERE id=?
            """,
            (
                utc_now(),
                status,
                int(payload.get("stale_categories") or 0),
                int(payload.get("refreshed_tickers") or 0),
                int(payload.get("provider_calls_skipped") or 0),
                int(payload.get("fallbacks_used") or 0),
                message or payload.get("message") or status,
                json_dumps(payload)[:50000],
                run_id,
            ),
        )
        state = conn.execute(
            "SELECT active_run_id FROM auto_agent_state WHERE lock_name = ?",
            (AUTO_AGENT_LOCK_NAME,),
        ).fetchone()
        if state and state["active_run_id"] == run_id:
            _clear_auto_agent_lock(conn)


def get_auto_agent_runs(limit: int = 25) -> list[dict[str, Any]]:
    rows = fetchall_with_schema(
        "SELECT * FROM auto_agent_runs ORDER BY started_at DESC, id DESC LIMIT ?",
        (max(1, min(int(limit), 100)),),
    )
    return [_row_to_auto_agent_run(row) for row in rows]


def get_auto_agent_latest() -> dict[str, Any] | None:
    rows = get_auto_agent_runs(limit=1)
    return rows[0] if rows else None
