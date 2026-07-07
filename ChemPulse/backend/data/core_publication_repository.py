from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any

import duckdb

from backend.data.db import get_connection
from backend.data.db import is_transient_duckdb_error
from backend.data.publication_relevance import MEDIUM_RELEVANCE_THRESHOLD, publication_matches_focus, publication_relevance
from backend.data.schemas import CORE_INGESTION_SCHEMA_SQL

ORPHANED_RUN_MESSAGE = "Run stopped unexpectedly and was closed by the scheduler watchdog."
SUPERSEDED_RUN_MESSAGE = "Run was superseded by a later successful ingestion."
LEGACY_ORPHANED_RUN_MESSAGE = "Run did not finish; marked failed before the next scheduled ingestion."

def ensure_core_ingestion_schema() -> None:
    with _get_connection_with_retry(read_only=False) as con:
        con.execute(CORE_INGESTION_SCHEMA_SQL)
        con.execute("ALTER TABLE core_ingestion_runs ADD COLUMN IF NOT EXISTS initial_query VARCHAR")
        con.execute("ALTER TABLE core_ingestion_runs ADD COLUMN IF NOT EXISTS downloaded_count INTEGER")
        con.execute("ALTER TABLE core_ingestion_runs ADD COLUMN IF NOT EXISTS diagnosis_path VARCHAR")
        con.execute("ALTER TABLE core_ingestion_cursors ADD COLUMN IF NOT EXISTS metadata_json VARCHAR")
        # Meta-OS M7 visible-publication fields (additive; never destructive).
        con.execute("ALTER TABLE bronze_core_publications ADD COLUMN IF NOT EXISTS matched_topic VARCHAR")
        con.execute("ALTER TABLE bronze_core_publications ADD COLUMN IF NOT EXISTS scaffold VARCHAR")
        con.execute("ALTER TABLE bronze_core_publications ADD COLUMN IF NOT EXISTS file_path VARCHAR")
        con.execute("ALTER TABLE bronze_core_publications ADD COLUMN IF NOT EXISTS duplicate_status VARCHAR")
        con.execute("ALTER TABLE bronze_core_publications ADD COLUMN IF NOT EXISTS run_folder VARCHAR")
        
class CorePublicationRepository:
    @staticmethod
    def reconcile_orphaned_runs(max_age_hours: float = 6) -> dict[str, int]:
        return {
            "superseded_running": CorePublicationRepository.mark_superseded_running_runs(),
            "superseded_legacy_failures": CorePublicationRepository.mark_superseded_legacy_failures(),
            "stale_failed": CorePublicationRepository.mark_stale_running_runs_failed(max_age_hours=max_age_hours),
        }
        
    @staticmethod
    def mark_superseded_running_runs() -> int:
        ensure_core_ingestion_schema()
        with _get_connection_with_retry(read_only=False) as con:
            result = con.execute(
                """
                UPDATE core_ingestion_runs AS run
                SET
                    finished_at = ?,
                    status = 'superseded',
                    error_message = ?
                WHERE run.status = 'running'
                  AND EXISTS (
                    SELECT 1
                    FROM core_ingestion_runs AS success
                    WHERE success.status = 'succeeded'
                      AND success.started_at > run.started_at
                  )
                RETURNING run_id
                """,
                [_utc_now(), SUPERSEDED_RUN_MESSAGE],
            ).fetchall()
        return len(result)

    @staticmethod
    def mark_superseded_legacy_failures() -> int:
        ensure_core_ingestion_schema()
        with _get_connection_with_retry(read_only=False) as con:
            result = con.execute(
                """
                UPDATE core_ingestion_runs AS run
                SET
                    status = 'superseded',
                    error_message = ?
                WHERE run.status = 'failed'
                  AND run.error_message IN (?, ?)
                  AND EXISTS (
                    SELECT 1
                    FROM core_ingestion_runs AS success
                    WHERE success.status = 'succeeded'
                      AND success.started_at > run.started_at
                  )
                RETURNING run_id
                """,
                [SUPERSEDED_RUN_MESSAGE, LEGACY_ORPHANED_RUN_MESSAGE, ORPHANED_RUN_MESSAGE],
            ).fetchall()
        return len(result)

    @staticmethod
    def mark_stale_running_runs_failed(max_age_hours: float = 6) -> int:
        ensure_core_ingestion_schema()
        with _get_connection_with_retry(read_only=False) as con:
            result = con.execute(
                """
                UPDATE core_ingestion_runs
                SET
                    finished_at = ?,
                    status = 'failed',
                    error_message = ?
                WHERE status = 'running'
                  AND started_at < (? - (? * INTERVAL '1 hour'))
                RETURNING run_id
                """,
                [_utc_now(), ORPHANED_RUN_MESSAGE, _utc_now(), max_age_hours],
            ).fetchall()
        return len(result)

    @staticmethod
    def start_run(run_id: str, query: str, requested_limit: int, page_size: int, initial_query: str | None = None) -> None:
        ensure_core_ingestion_schema()
        with _get_connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO core_ingestion_runs (
                    run_id, started_at, finished_at, query, initial_query, status, requested_limit,
                    page_size, downloaded_count, inserted_count, updated_count, diagnosis_path, error_message
                )
                VALUES (?, ?, NULL, ?, ?, 'running', ?, ?, 0, 0, 0, NULL, NULL)
                """,
                [run_id, _utc_now(), query, initial_query or query, requested_limit, page_size],
            )

    @staticmethod
    def update_run_query(run_id: str, query: str) -> None:
        with _get_connection_with_retry(read_only=False) as con:
            con.execute(
                """
                UPDATE core_ingestion_runs
                SET query = ?
                WHERE run_id = ?
                """,
                [query, run_id],
            )

    @staticmethod
    def finish_run(
        run_id: str,
        status: str,
        inserted_count: int,
        updated_count: int,
        error_message: str | None = None,
        *,
        downloaded_count: int = 0,
        diagnosis_path: str | None = None,
    ) -> None:
        with _get_connection_with_retry(read_only=False) as con:
            con.execute(
                """
                UPDATE core_ingestion_runs
                SET
                    finished_at = ?,
                    status = ?,
                    downloaded_count = ?,
                    inserted_count = ?,
                    updated_count = ?,
                    diagnosis_path = ?,
                    error_message = ?
                WHERE run_id = ?
                """,
                [_utc_now(), status, downloaded_count, inserted_count, updated_count, diagnosis_path, error_message, run_id],
            )

    def upsert_publications(publications: list[dict[str, Any]], query: str) -> dict[str, int]:
        ensure_core_ingestion_schema()
        inserted = 0
        updated = 0
        inserted_items: list[dict[str, str]] = []
        updated_items: list[dict[str, str]] = []
        fetched_at = _utc_now()

        with _get_connection_with_retry(read_only=False) as con:
            for publication in publications:
                core_id = str(publication["core_id"])
                existed = _publication_exists(con, core_id)
                con.execute(
                    """
                    INSERT INTO bronze_core_publications (
                        core_id, title, doi, year_published, published_date,
                        authors_json, journal, abstract, topics_json, full_text_url,
                        source_url, raw_json, query, fetched_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(core_id) DO UPDATE SET
                        title = excluded.title,
                        doi = excluded.doi,
                        year_published = excluded.year_published,
                        published_date = excluded.published_date,
                        authors_json = excluded.authors_json,
                        journal = excluded.journal,
                        abstract = excluded.abstract,
                        topics_json = excluded.topics_json,
                        full_text_url = excluded.full_text_url,
                        source_url = excluded.source_url,
                        raw_json = excluded.raw_json,
                        query = excluded.query,
                        fetched_at = excluded.fetched_at
                    """,
                    [
                        core_id,
                        publication["title"],
                        publication.get("doi"),
                        publication.get("year_published"),
                        publication.get("published_date"),
                        json.dumps(publication.get("authors", []), ensure_ascii=True),
                        publication.get("journal"),
                        publication.get("abstract"),
                        json.dumps(publication.get("topics", []), ensure_ascii=True),
                        publication.get("full_text_url"),
                        publication.get("source_url"),
                        json.dumps(publication.get("raw", {}), ensure_ascii=True),
                        query,
                        fetched_at,
                    ],
                )
                if existed:
                    updated += 1
                    updated_items.append(_change_item(publication))
                else:
                    inserted += 1
                    inserted_items.append(_change_item(publication))

        return {
            "inserted": inserted,
            "updated": updated,
            "inserted_items": inserted_items,
            "updated_items": updated_items,
        }

    @staticmethod
    def annotate_publication(
        core_id: str,
        *,
        matched_topic: str | None = None,
        scaffold: str | None = None,
        file_path: str | None = None,
        duplicate_status: str | None = None,
        run_folder: str | None = None,
    ) -> None:
        """Set Meta-OS M7 visible fields on an already-stored publication. Only non-None
        values are written, so this never clobbers existing data with blanks."""
        ensure_core_ingestion_schema()
        with _get_connection_with_retry(read_only=False) as con:
            if matched_topic is not None:
                con.execute(
                    "UPDATE bronze_core_publications SET matched_topic = ? WHERE core_id = ?",
                    [matched_topic, str(core_id)],
                )
            if scaffold is not None:
                con.execute(
                    "UPDATE bronze_core_publications SET scaffold = ? WHERE core_id = ?",
                    [scaffold, str(core_id)],
                )
            if file_path is not None:
                con.execute(
                    "UPDATE bronze_core_publications SET file_path = ? WHERE core_id = ?",
                    [file_path, str(core_id)],
                )
            if duplicate_status is not None:
                con.execute(
                    "UPDATE bronze_core_publications SET duplicate_status = ? WHERE core_id = ?",
                    [duplicate_status, str(core_id)],
                )
            if run_folder is not None:
                con.execute(
                    "UPDATE bronze_core_publications SET run_folder = ? WHERE core_id = ?",
                    [run_folder, str(core_id)],
                )

    @staticmethod
    def existing_core_ids(core_ids: list[str]) -> set[str]:
        ensure_core_ingestion_schema()
        cleaned_ids = [str(core_id) for core_id in core_ids if str(core_id)]
        if not cleaned_ids:
            return set()
        placeholders = ", ".join(["?"] * len(cleaned_ids))
        with get_connection(read_only=True) as con:
            rows = con.execute(
                f"SELECT core_id FROM bronze_core_publications WHERE core_id IN ({placeholders})",
                cleaned_ids,
            ).fetchall()
        return {str(row[0]) for row in rows}

    @staticmethod
    def latest_successful_run_started_at() -> datetime | None:
        ensure_core_ingestion_schema()
        with get_connection(read_only=True) as con:
            row = con.execute(
                """
                SELECT started_at
                FROM core_ingestion_runs
                WHERE status = 'succeeded'
                ORDER BY started_at DESC
                LIMIT 1
                """
            ).fetchone()
        value = row[0] if row else None
        # DuckDB returns TIMESTAMP as a tz-naive datetime even though we store UTC
        # (_utc_now). Restore the UTC tzinfo so callers can compare against tz-aware
        # datetime.now(timezone.utc) without an offset-naive/aware TypeError.
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    @staticmethod
    def ingestion_cursor(source: str = "core") -> dict[str, Any] | None:
        ensure_core_ingestion_schema()
        with get_connection(read_only=True) as con:
            row = con.execute(
                """
                SELECT source, frontier_core_id, frontier_published_date, query, updated_at, metadata_json
                FROM core_ingestion_cursors
                WHERE source = ?
                LIMIT 1
                """,
                [source],
            ).fetchone()
        return _cursor_record(row) if row else None

    @staticmethod
    def upsert_ingestion_cursor(
        source: str,
        frontier_core_id: str,
        frontier_published_date: str,
        query: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ensure_core_ingestion_schema()
        with _get_connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO core_ingestion_cursors (
                    source, frontier_core_id, frontier_published_date, query, updated_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source) DO UPDATE SET
                    frontier_core_id = excluded.frontier_core_id,
                    frontier_published_date = excluded.frontier_published_date,
                    query = excluded.query,
                    updated_at = excluded.updated_at,
                    metadata_json = excluded.metadata_json
                """,
                [
                    source,
                    frontier_core_id,
                    frontier_published_date,
                    query,
                    _utc_now(),
                    json.dumps(metadata or {}, ensure_ascii=True),
                ],
            )

    @staticmethod
    def publication_metrics() -> dict[str, Any]:
        ensure_core_ingestion_schema()
        with get_connection(read_only=True) as con:
            publication_row = con.execute(
                """
                SELECT
                    COUNT(*)::INTEGER AS publication_count,
                    COUNT(DISTINCT journal)::INTEGER AS journal_count,
                    MAX(fetched_at) AS latest_fetch_at
                FROM bronze_core_publications
                """
            ).fetchone()
            run_row = con.execute(
                """
                SELECT
                    run.status,
                    run.inserted_count,
                    run.updated_count,
                    run.error_message,
                    run.finished_at
                FROM core_ingestion_runs
                AS run
                WHERE run.status <> 'superseded'
                ORDER BY run.started_at DESC
                LIMIT 1
                """
            ).fetchone()

        metrics = {
            "publication_count": publication_row[0] if publication_row else 0,
            "journal_count": publication_row[1] if publication_row else 0,
            "latest_fetch_at": publication_row[2] if publication_row else None,
            "last_run_status": "never run",
            "last_run_delta": "0 new / 0 updated",
            "last_run_error": "",
        }
        if run_row:
            metrics["last_run_status"] = run_row[0]
            metrics["last_run_delta"] = f"{run_row[1]} new / {run_row[2]} updated"
            metrics["last_run_error"] = run_row[3] or ""
        return metrics

    @staticmethod
    def agent_run_status() -> dict[str, Any]:
        ensure_core_ingestion_schema()
        with get_connection(read_only=True) as con:
            latest_update = con.execute("SELECT MAX(fetched_at) FROM bronze_core_publications").fetchone()
            last_success = con.execute(
                """
                SELECT run_id, started_at, finished_at, status, query, downloaded_count, inserted_count, updated_count, diagnosis_path, error_message
                FROM core_ingestion_runs
                WHERE status = 'succeeded'
                ORDER BY finished_at DESC NULLS LAST, started_at DESC
                LIMIT 1
                """
            ).fetchone()
            last_insufficient = con.execute(
                """
                SELECT run_id, started_at, finished_at, status, query, downloaded_count, inserted_count, updated_count, diagnosis_path, error_message
                FROM core_ingestion_runs
                WHERE status = 'insufficient'
                ORDER BY finished_at DESC NULLS LAST, started_at DESC
                LIMIT 1
                """
            ).fetchone()
            last_failure = con.execute(
                """
                SELECT run_id, started_at, finished_at, status, query, downloaded_count, inserted_count, updated_count, diagnosis_path, error_message
                FROM core_ingestion_runs
                WHERE status = 'failed'
                ORDER BY finished_at DESC NULLS LAST, started_at DESC
                LIMIT 1
                """
            ).fetchone()
            latest_run = con.execute(
                """
                SELECT
                    run.run_id,
                    run.started_at,
                    run.finished_at,
                    run.status,
                    run.query,
                    run.downloaded_count,
                    run.inserted_count,
                    run.updated_count,
                    run.diagnosis_path,
                    run.error_message
                FROM core_ingestion_runs AS run
                WHERE run.status <> 'superseded'
                ORDER BY run.started_at DESC
                LIMIT 1
                """
            ).fetchone()

        return {
            "last_database_update": latest_update[0] if latest_update else None,
            "last_success": _run_record(last_success, "succeeded") if last_success else None,
            "last_insufficient": _run_record(last_insufficient, "insufficient") if last_insufficient else None,
            "last_failure": _run_record(last_failure, "failed") if last_failure else None,
            "latest_run": _run_record(latest_run, latest_run[3]) if latest_run else None,
        }

    @staticmethod
    def recent_publications(limit: int = 6, query: str = "") -> list[dict[str, Any]]:
        ensure_core_ingestion_schema()
        params: list[Any] = []
        where_clause = ""
        if query.strip():
            term = f"%{query.strip().lower()}%"
            where_clause = """
            WHERE
                LOWER(title) LIKE ?
                OR LOWER(COALESCE(abstract, '')) LIKE ?
                OR LOWER(COALESCE(journal, '')) LIKE ?
                OR LOWER(COALESCE(doi, '')) LIKE ?
            """
            params.extend([term, term, term, term])

        fetch_limit = max(limit * 4, limit)
        params.append(fetch_limit)
        with get_connection(read_only=True) as con:
            cards = [
                _publication_card(row)
                for row in con.execute(
                    f"""
                    SELECT
                        core_id, title, doi, year_published, journal, abstract,
                        authors_json, topics_json, full_text_url, source_url, fetched_at
                    FROM bronze_core_publications
                    {where_clause}
                    ORDER BY fetched_at DESC, year_published DESC NULLS LAST, title ASC
                    LIMIT ?
                    """,
                    params,
                ).fetchall()
            ]
        filtered_cards = [
            card
            for card in cards
            if query.strip()
            or (
                int(card["relevance_score"] or 0) >= MEDIUM_RELEVANCE_THRESHOLD
                and publication_matches_focus(card["title"], card["summary"], card["journal"], card["topics"])
            )
        ]
        return filtered_cards[:limit]

    @staticmethod
    def top_journals(limit: int = 5) -> list[dict[str, Any]]:
        ensure_core_ingestion_schema()
        with get_connection(read_only=True) as con:
            rows = con.execute(
                """
                SELECT COALESCE(NULLIF(journal, ''), 'Unknown source') AS label, COUNT(*)::INTEGER AS count
                FROM bronze_core_publications
                GROUP BY label
                ORDER BY count DESC, label ASC
                LIMIT ?
                """,
                [limit],
            ).fetchall()
        return [{"label": row[0], "count": row[1]} for row in rows]

    @staticmethod
    def available_journals() -> list[str]:
        ensure_core_ingestion_schema()
        with get_connection(read_only=True) as con:
            rows = con.execute(
                """
                SELECT COALESCE(NULLIF(journal, ''), 'Unknown source') AS journal
                FROM bronze_core_publications
                GROUP BY journal
                ORDER BY journal ASC
                """
            ).fetchall()
        return [str(row[0]) for row in rows]

    @staticmethod
    def journal_publication_texts(journal: str = "") -> list[dict[str, Any]]:
        ensure_core_ingestion_schema()
        params: list[Any] = []
        where_clause = ""
        if journal.strip():
            where_clause = "WHERE COALESCE(NULLIF(journal, ''), 'Unknown source') = ?"
            params.append(journal.strip())
        with get_connection(read_only=True) as con:
            rows = con.execute(
                f"""
                SELECT
                    core_id,
                    title,
                    abstract,
                    topics_json,
                    COALESCE(NULLIF(journal, ''), 'Unknown source') AS journal,
                    year_published,
                    fetched_at
                FROM bronze_core_publications
                {where_clause}
                ORDER BY year_published ASC NULLS LAST, fetched_at ASC, title ASC
                """,
                params,
            ).fetchall()
        records = []
        for row in rows:
            try:
                topics = " ".join(json.loads(row[3] or "[]"))
            except json.JSONDecodeError:
                topics = str(row[3] or "")
            records.append(
                {
                    "core_id": row[0],
                    "title": row[1] or "",
                    "abstract": row[2] or "",
                    "topics": topics,
                    "journal": row[4],
                    "year": row[5],
                    "fetched_at": row[6],
                }
            )
        return records

def _publication_exists(con: duckdb.DuckDBPyConnection, core_id: str) -> bool:
    row = con.execute("SELECT 1 FROM bronze_core_publications WHERE core_id = ? LIMIT 1", [core_id]).fetchone()
    return bool(row)

def _run_record(row: tuple[Any, ...], status: str) -> dict[str, Any]:
    if len(row) >= 10 and row[3] in {"running", "succeeded", "failed", "insufficient", "superseded"}:
        run_id, started_at, finished_at, status, query, downloaded_count, inserted_count, updated_count, diagnosis_path, error_message = row[:10]
    elif len(row) >= 7 and row[3] in {"running", "succeeded", "failed", "superseded"}:
        run_id, started_at, finished_at, status, inserted_count, updated_count, error_message = row[:7]
        query = ""
        downloaded_count = 0
        diagnosis_path = ""
    elif status == "failed":
        run_id, started_at, finished_at, inserted_count, updated_count, error_message = row[:6]
        query = ""
        downloaded_count = 0
        diagnosis_path = ""
    else:
        run_id, started_at, finished_at, inserted_count, updated_count = row[:5]
        query = ""
        downloaded_count = 0
        diagnosis_path = ""
        error_message = row[6] if len(row) > 6 else ""
    return {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "query": str(query or ""),
        "downloaded_count": int(downloaded_count or 0),
        "records_processed": int(inserted_count or 0) + int(updated_count or 0),
        "inserted_count": int(inserted_count or 0),
        "updated_count": int(updated_count or 0),
        "diagnosis_path": str(diagnosis_path or ""),
        "error_summary": _redact_secret(str(error_message or "")),
    }

def _cursor_record(row: tuple[Any, ...]) -> dict[str, Any]:
    metadata: dict[str, Any]
    try:
        metadata = json.loads(row[5] or "{}")
    except json.JSONDecodeError:
        metadata = {}
    return {
        "source": str(row[0] or "core"),
        "frontier_core_id": str(row[1] or ""),
        "frontier_published_date": str(row[2] or ""),
        "query": str(row[3] or ""),
        "updated_at": row[4],
        "metadata": metadata,
    }

def _redact_secret(message: str) -> str:
    if not message:
        return ""
    redacted = re.sub(r"CORE_API_KEY\s*=\s*[^,\s;]+", "literature API key [redacted]", message)
    redacted = redacted.replace("CORE_API_KEY", "literature API key")
    redacted = re.sub(r"sk-[A-Za-z0-9_\-]+", "[redacted]", redacted)
    redacted = re.sub(r"LSl[A-Za-z0-9_\-]+", "[redacted]", redacted)
    return redacted

def _get_connection_with_retry(read_only: bool = False, attempts: int = 60, delay_seconds: float = 2.0) -> duckdb.DuckDBPyConnection:
    last_error: duckdb.Error | None = None
    for _ in range(attempts):
        try:
            return get_connection(read_only=read_only)
        except duckdb.Error as exc:
            last_error = exc
            if not _is_lock_error(exc):
                raise
            time.sleep(delay_seconds)
    raise RuntimeError(f"Timed out waiting for DuckDB database lock: {last_error}")

def _is_lock_error(exc: duckdb.Error) -> bool:
    return is_transient_duckdb_error(exc)

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _publication_card(row: tuple[Any, ...]) -> dict[str, Any]:
    authors = json.loads(row[6] or "[]")
    topics = json.loads(row[7] or "[]")
    abstract = row[5] or ""
    title = row[1]
    journal = row[4] or "Unknown source"
    topics_text = ", ".join(topics)
    relevance_score, relevance_level = _publication_relevance(title, abstract, journal, topics_text)
    return {
        "core_id": row[0],
        "title": title,
        "doi": row[2] or "",
        "year": _display_year(row[3]),
        "journal": journal,
        "summary": abstract[:220] + ("..." if len(abstract) > 220 else ""),
        "authors": ", ".join(authors[:3]) if authors else "Unknown authors",
        "topics": ", ".join(topics[:3]) if topics else "No topics",
        "url": row[8] or row[9] or "",
        "fetched_at": row[10].isoformat() if row[10] else "",
        "relevance_score": relevance_score,
        "relevance_level": relevance_level,
    }

def _change_item(publication: dict[str, Any]) -> dict[str, str]:
    return {
        "core_id": str(publication.get("core_id", "")),
        "title": str(publication.get("title", "")),
        "doi": str(publication.get("doi") or ""),
        "journal": str(publication.get("journal") or "Unknown source"),
        "year": _display_year(publication.get("year_published")),
    }

def _display_year(value: Any) -> str:
    try:
        year = int(value)
    except (TypeError, ValueError):
        return "n/a"
    current_year = datetime.now(timezone.utc).year
    if year < 1800 or year > current_year + 1:
        return "n/a"
    return str(year)

def _publication_relevance(title: str, abstract: str, journal: str, topics: str) -> tuple[int, str]:
    return publication_relevance(title, abstract, journal, topics)


