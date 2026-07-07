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