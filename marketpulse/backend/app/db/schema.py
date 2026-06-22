from __future__ import annotations

from app.db.connection import connect

AUTO_AGENT_LOCK_NAME = "auto_cached_agent"


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS api_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                category TEXT NOT NULL,
                symbol TEXT,
                period TEXT,
                event_date TEXT,
                value_primary REAL,
                value_secondary REAL,
                sentiment_score REAL,
                title TEXT,
                summary TEXT,
                url TEXT,
                raw_json TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_api_records_provider ON api_records(provider);
            CREATE INDEX IF NOT EXISTS idx_api_records_symbol ON api_records(symbol);
            CREATE INDEX IF NOT EXISTS idx_api_records_category ON api_records(category);
            CREATE INDEX IF NOT EXISTS idx_api_records_event_date ON api_records(event_date);
            CREATE INDEX IF NOT EXISTS idx_api_records_created_at ON api_records(created_at);

            CREATE TABLE IF NOT EXISTS provider_status (
                provider TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                message TEXT,
                last_success_at TEXT,
                last_attempt_at TEXT NOT NULL,
                raw_json TEXT
            );

            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                symbol TEXT,
                topic_id INTEGER,
                label TEXT,
                keywords TEXT,
                weight REAL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS refresh_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                tickers TEXT,
                message TEXT,
                raw_json TEXT
            );

            CREATE TABLE IF NOT EXISTS auto_agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                mode TEXT NOT NULL,
                tickers TEXT,
                stale_categories INTEGER DEFAULT 0,
                refreshed_tickers INTEGER DEFAULT 0,
                provider_calls_skipped INTEGER DEFAULT 0,
                fallbacks_used INTEGER DEFAULT 0,
                message TEXT,
                raw_json TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_auto_agent_runs_started_at ON auto_agent_runs(started_at);

            CREATE TABLE IF NOT EXISTS auto_agent_state (
                lock_name TEXT PRIMARY KEY,
                active_run_id INTEGER,
                mode TEXT,
                tickers TEXT,
                claimed_at TEXT,
                heartbeat_at TEXT,
                message TEXT
            );

            CREATE TABLE IF NOT EXISTS watchlist_tickers (
                ticker TEXT PRIMARY KEY,
                position INTEGER NOT NULL,
                source TEXT NOT NULL,
                added_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_watchlist_tickers_position ON watchlist_tickers(position);

            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                report_date TEXT NOT NULL,
                scope TEXT NOT NULL,
                ticker TEXT,
                period TEXT,
                title TEXT,
                report_text TEXT NOT NULL,
                raw_json TEXT,
                run_id INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_daily_reports_created_at ON daily_reports(created_at);
            CREATE INDEX IF NOT EXISTS idx_daily_reports_scope ON daily_reports(scope);
            CREATE INDEX IF NOT EXISTS idx_daily_reports_ticker ON daily_reports(ticker);
            """
        )
