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

def available_table_name(*candidates: str) -> str | None:
    for candidate in candidates:
        if table_exists(candidate):
            return candidate
    return None

def query_records(sql: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    with get_connection(read_only=True) as con:
        cursor = con.execute(sql, list(params or []))
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

def _connect_with_retry(db_path: Path) -> duckdb.DuckDBPyConnection:
    last_error: Exception | None = None
    deadline = time.monotonic() + _db_connect_timeout_seconds()
    while True:
        try:
            return duckdb.connect(str(db_path), read_only=False)
        except duckdb.Error as exc:
            last_error = exc
            if not is_transient_duckdb_error(exc) or time.monotonic() >= deadline:
                raise
            time.sleep(0.25)
        except OSError as exc:
            last_error = exc
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.25)

def _db_connect_timeout_seconds() -> float:
    try:
        return max(float(os.getenv("CHEMPULSE_DB_CONNECT_TIMEOUT", "45")), 1.0)
    except ValueError:
        return 45.0

def is_transient_duckdb_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "lock",
            "being used by another process",
            "cannot open file",
            "unique file handle conflict",
            "already attached",
            "different configuration than existing connections",
        )
    )

class _DatabaseFileLock:
    def __init__(self, db_path: Path) -> None:
        self.lock_path = db_path.with_suffix(db_path.suffix + ".lock")
        self._handle = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.lock_path.open("a+b")
        deadline = time.monotonic() + _db_connect_timeout_seconds()
        while True:
            try:
                _lock_handle(self._handle)
                return
            except OSError:
                if time.monotonic() >= deadline:
                    self.release()
                    raise TimeoutError(f"Timed out waiting for ChemPulse database lock: {self.lock_path}")
                time.sleep(0.25)

    def release(self) -> None:
        if not self._handle:
            return
        try:
            _unlock_handle(self._handle)
        finally:
            self._handle.close()
            self._handle = None

if os.name == "nt":
    import msvcrt

    def _lock_handle(handle) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock_handle(handle) -> None:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass

else:
    import fcntl

    def _lock_handle(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_handle(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
