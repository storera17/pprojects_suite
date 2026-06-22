from __future__ import annotations

import sqlite3
from typing import Any

from app.core.config import settings
from app.db.connection import connect, fetchall_with_schema, utc_now


def _normalize_watchlist_tickers(tickers: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for ticker in tickers or []:
        clean = str(ticker or "").strip().upper()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        ordered.append(clean)
    return ordered


def _insert_watchlist_rows(conn: sqlite3.Connection, tickers: list[str], source: str) -> None:
    max_position_row = conn.execute(
        "SELECT COALESCE(MAX(position), 0) AS max_position FROM watchlist_tickers"
    ).fetchone()
    next_position = int(max_position_row["max_position"] or 0) + 1
    for ticker in tickers:
        exists = conn.execute("SELECT 1 FROM watchlist_tickers WHERE ticker = ?", (ticker,)).fetchone()
        if exists:
            continue
        conn.execute(
            """
            INSERT INTO watchlist_tickers(ticker, position, source, added_at)
            VALUES (?, ?, ?, ?)
            """,
            (ticker, next_position, source, utc_now()),
        )
        next_position += 1


def seed_watchlist(tickers: list[str] | tuple[str, ...] | None, source: str = "config_seed") -> list[str]:
    normalized = _normalize_watchlist_tickers(tickers)
    if not normalized:
        return []
    with connect() as conn:
        _insert_watchlist_rows(conn, normalized, source)
    return normalized


def get_watchlist_tickers(limit: int | None = None) -> list[str]:
    seed_watchlist(settings.watchlist_seed_tickers, source="config_seed")
    sql = "SELECT ticker FROM watchlist_tickers ORDER BY position ASC, added_at ASC"
    params: tuple[Any, ...] = ()
    if limit is not None:
        sql += " LIMIT ?"
        params = (max(1, int(limit)),)
    return [str(row["ticker"]).upper() for row in fetchall_with_schema(sql, params)]


def add_watchlist_ticker(ticker: str, source: str = "validated_ticker") -> list[str]:
    clean = str(ticker or "").strip().upper()
    if not clean:
        return get_watchlist_tickers()
    seed_watchlist(settings.watchlist_seed_tickers, source="config_seed")
    with connect() as conn:
        exists = conn.execute("SELECT 1 FROM watchlist_tickers WHERE ticker = ?", (clean,)).fetchone()
        if not exists:
            max_position_row = conn.execute(
                "SELECT COALESCE(MAX(position), 0) AS max_position FROM watchlist_tickers"
            ).fetchone()
            next_position = int(max_position_row["max_position"] or 0) + 1
            conn.execute(
                """
                INSERT INTO watchlist_tickers(ticker, position, source, added_at)
                VALUES (?, ?, ?, ?)
                """,
                (clean, next_position, source, utc_now()),
            )
    return get_watchlist_tickers()
