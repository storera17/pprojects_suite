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
