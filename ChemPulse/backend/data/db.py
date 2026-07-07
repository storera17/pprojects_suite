from __future__ import annotations

from pathlib import Path
import os
import threading
import time
from typing import Any, Iterable

import duckdb

from backend.config import get_config
from backend.data.schemas import GOLD_SCHEMA_SQL, REQUIRED_GOLD_TABLES

_db_lock = threading.RLock()

def get_db_path() -> Path:
    return get_config().database_path

class _LockedConnection:
    def __init__(self, connection: duckdb.DuckDBPyConnection, file_lock: "_DatabaseFileLock") -> None:
        self._connection = connection
        self._file_lock = file_lock
        self._closed = False

    def __enter__(self) -> duckdb.DuckDBPyConnection:
        return self._connection

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._connection.close()
        finally:
            try:
                self._file_lock.release()
            finally:
                _db_lock.release()

    def close(self) -> None:
        self.__exit__(None, None, None)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

def get_connection(read_only: bool = False) -> _LockedConnection:
    # DuckDB rejects mixed read-only/read-write connections to the same file
    # inside one process. ChemPulse has background writes and dashboard reads,
    # so serialize local and cross-process access and keep all connections on
    # one configuration.
    _db_lock.acquire()
    file_lock: _DatabaseFileLock | None = None
    try:
        db_path = get_db_path()
        file_lock = _DatabaseFileLock(db_path)
        file_lock.acquire()
        return _LockedConnection(_connect_with_retry(db_path), file_lock)
    except Exception:
        if file_lock:
            file_lock.release()
        _db_lock.release()
        raise

def ensure_database_exists() -> Path:
    db_path = get_db_path()
    if db_path.exists() and all(table_exists(table_name) for table_name in REQUIRED_GOLD_TABLES):
        return db_path

    return initialize_schema(db_path)

def initialize_schema(db_path: str | Path | None = None) -> Path:
    final_path = Path(db_path) if db_path else get_db_path()
    final_path.parent.mkdir(parents=True, exist_ok=True)
    _db_lock.acquire()
    file_lock = _DatabaseFileLock(final_path)
    try:
        file_lock.acquire()
        with duckdb.connect(str(final_path)) as con:
            con.execute(GOLD_SCHEMA_SQL)
    finally:
        try:
            file_lock.release()
        finally:
            _db_lock.release()
    return final_path

def table_exists(table_name: str) -> bool:
    with get_connection(read_only=True) as con:
        result = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = CURRENT_SCHEMA() AND table_name = ?",
            [table_name],
        ).fetchone()
    return bool(result and result[0])
