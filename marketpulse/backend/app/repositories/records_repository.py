from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.connection import connect, fetchall_with_schema, json_dumps, utc_now


def insert_record(
    provider: str,
    category: str,
    symbol: str | None = None,
    period: str | None = None,
    event_date: str | None = None,
    value_primary: float | None = None,
    value_secondary: float | None = None,
    sentiment_score: float | None = None,
    title: str | None = None,
    summary: str | None = None,
    url: str | None = None,
    raw_json: Any | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO api_records (
                provider, category, symbol, period, event_date, value_primary, value_secondary,
                sentiment_score, title, summary, url, raw_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                provider,
                category,
                symbol.upper() if symbol else None,
                period,
                event_date,
                value_primary,
                value_secondary,
                sentiment_score,
                title,
                summary,
                url,
                json_dumps(raw_json) if raw_json is not None else None,
                utc_now(),
            ),
        )


def recent_records(
    provider: str | None = None,
    category: str | None = None,
    symbol: str | None = None,
    days: int = 365,
    limit: int = 500,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if category:
        clauses.append("category = ?")
        params.append(category)
    if symbol:
        clauses.append("(symbol = ? OR symbol IS NULL)")
        params.append(symbol.upper())
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max(1, days))).date().isoformat()
    clauses.append("(event_date IS NULL OR event_date >= ?)")
    params.append(cutoff)
    params.append(limit)
    sql = (
        f"SELECT * FROM api_records WHERE {' AND '.join(clauses)} "
        "ORDER BY COALESCE(event_date, created_at) DESC, id DESC LIMIT ?"
    )
    return [dict(row) for row in fetchall_with_schema(sql, params)]


def latest_records(
    provider: str,
    category: str | None = None,
    symbol: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses = ["provider = ?"]
    params: list[Any] = [provider]
    if category:
        clauses.append("category = ?")
        params.append(category)
    if symbol:
        clauses.append("symbol = ?")
        params.append(symbol.upper())
    params.append(limit)
    sql = f"SELECT * FROM api_records WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id DESC LIMIT ?"
    return [dict(row) for row in fetchall_with_schema(sql, params)]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _cache_age_fields(created_at: str | None, ttl_seconds: int | None = None) -> dict[str, Any]:
    parsed = _parse_dt(created_at)
    if not parsed:
        return {
            "cache_collected_at": created_at,
            "cache_age_seconds": None,
            "cache_age_minutes": None,
            "cache_fresh": False,
        }
    age_seconds = max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))
    return {
        "cache_collected_at": created_at,
        "cache_age_seconds": age_seconds,
        "cache_age_minutes": round(age_seconds / 60, 2),
        "cache_fresh": bool(ttl_seconds is not None and age_seconds <= ttl_seconds),
    }


def cache_snapshot(
    provider: str,
    category: str | None = None,
    symbol: str | None = None,
    ttl_seconds: int = 86400,
    limit: int = 500,
) -> dict[str, Any]:
    rows = latest_records(provider=provider, category=category, symbol=symbol, limit=limit)
    latest_created = rows[0].get("created_at") if rows else None
    fields = _cache_age_fields(latest_created, ttl_seconds)
    return {
        "provider": provider,
        "category": category,
        "symbol": symbol.upper() if symbol else None,
        "rows": rows,
        "count": len(rows),
        "fresh": bool(rows and fields["cache_fresh"]),
        **fields,
    }


def insert_topics(source: str, symbol: str | None, topics: list[dict[str, Any]]) -> None:
    with connect() as conn:
        for topic in topics:
            conn.execute(
                """
                INSERT INTO topics(source, symbol, topic_id, label, keywords, weight, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    symbol.upper() if symbol else None,
                    int(topic.get("topic_id", 0)),
                    topic.get("label") or ", ".join(topic.get("keywords", [])[:4]),
                    json_dumps(topic.get("keywords", [])),
                    topic.get("weight"),
                    utc_now(),
                ),
            )


def get_topics(symbol: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if symbol:
        clauses.append("(symbol = ? OR symbol IS NULL)")
        params.append(symbol.upper())
    params.append(limit)
    rows = fetchall_with_schema(
        f"SELECT * FROM topics WHERE {' AND '.join(clauses)} ORDER BY created_at DESC, id DESC LIMIT ?",
        params,
    )
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["keywords"] = json.loads(item.get("keywords") or "[]")
        except Exception:
            item["keywords"] = []
        output.append(item)
    return output


def db_summary() -> dict[str, Any]:
    with connect() as conn:
        records = conn.execute(
            """
            SELECT provider, category, COUNT(*) AS n
            FROM api_records
            GROUP BY provider, category
            ORDER BY provider, category
            """
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) AS n FROM api_records").fetchone()["n"]
        topics = conn.execute("SELECT COUNT(*) AS n FROM topics").fetchone()["n"]
    return {
        "total_records": total,
        "topic_rows": topics,
        "by_provider_category": [dict(row) for row in records],
    }
