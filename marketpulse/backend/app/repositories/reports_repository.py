from __future__ import annotations

import json
from typing import Any

from app.db.connection import connect, fetchall_with_schema, fetchone_with_schema, json_dumps, utc_now


def save_daily_report(
    report_date: str,
    scope: str,
    ticker: str | None,
    period: str | None,
    title: str | None,
    report_text: str,
    raw_json: Any | None = None,
    run_id: int | None = None,
) -> int:
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO daily_reports(
                created_at, report_date, scope, ticker, period, title, report_text, raw_json, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now(),
                report_date,
                scope,
                ticker.upper() if ticker else None,
                period,
                title,
                report_text,
                json_dumps(raw_json)[:200000] if raw_json is not None else None,
                run_id,
            ),
        )
        return int(cursor.lastrowid)


def _row_to_daily_report(row) -> dict[str, Any]:
    item = dict(row)
    try:
        item["raw"] = json.loads(item.get("raw_json") or "{}")
    except Exception:
        item["raw"] = {}
    return item


def get_latest_daily_report(scope: str = "watchlist", ticker: str | None = None) -> dict[str, Any] | None:
    clauses = ["scope = ?"]
    params: list[Any] = [scope]
    if ticker:
        clauses.append("ticker = ?")
        params.append(ticker.upper())
    row = fetchone_with_schema(
        f"SELECT * FROM daily_reports WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id DESC LIMIT 1",
        params,
    )
    return _row_to_daily_report(row) if row else None


def get_daily_reports(limit: int = 20, scope: str | None = None, ticker: str | None = None) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if scope:
        clauses.append("scope = ?")
        params.append(scope)
    if ticker:
        clauses.append("ticker = ?")
        params.append(ticker.upper())
    params.append(max(1, min(int(limit), 200)))
    rows = fetchall_with_schema(
        f"SELECT * FROM daily_reports WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id DESC LIMIT ?",
        params,
    )
    return [_row_to_daily_report(row) for row in rows]
