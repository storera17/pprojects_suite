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
