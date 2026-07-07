from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.data.core_publication_repository import ensure_core_ingestion_schema
from backend.data.db import get_connection
from backend.services.run_health_service import RunHealthService


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    return tmp_path


def _seed(runs: list[tuple[str, int]]) -> None:
    """runs = list of (status, inserted) oldest→newest."""
    ensure_core_ingestion_schema()
    base = datetime(2026, 6, 1, tzinfo=timezone.utc)
    with get_connection(read_only=False) as con:
        for i, (status, inserted) in enumerate(runs):
            ts = base + timedelta(days=i)
            con.execute(
                "INSERT INTO core_ingestion_runs (run_id, started_at, finished_at, query, "
                "status, requested_limit, page_size, inserted_count, updated_count, error_message) "
                "VALUES (?, ?, ?, 'q', ?, 25, 25, ?, 0, ?)",
                [f"r{i}", ts, ts, status, inserted,
                 "boom" if status == "failed" else None],
            )


def test_empty_is_unknown():
    s = RunHealthService.summary()
    assert s["health"] == "unknown"
    assert s["consecutive_successful_runs"] == 0
    assert s["last_successful_run"] is None and s["last_failed_run"] is None


def test_consecutive_successful_counts_succeeded_and_insufficient():
    _seed([("failed", 0), ("succeeded", 25), ("insufficient", 3), ("succeeded", 20)])
    s = RunHealthService.summary()
    assert s["health"] == "healthy"
    assert s["consecutive_successful_runs"] == 3   # last three completed cleanly
    assert s["consecutive_failed_runs"] == 0
    assert s["last_successful_run"]["status"] == "succeeded"
    assert s["last_failed_run"]["status"] == "failed"


def test_consecutive_failed_and_failing_health():
    _seed([("succeeded", 25), ("failed", 0), ("failed", 0)])
    s = RunHealthService.summary()
    assert s["health"] == "failing"
    assert s["consecutive_failed_runs"] == 2
    assert s["consecutive_successful_runs"] == 0
    assert s["last_successful_run"]["status"] == "succeeded"
    assert "boom" in s["last_failed_run"]["error"]


def test_production_progress_threshold():
    _seed([("succeeded", 25)] * 7)
    s = RunHealthService.summary()
    assert s["consecutive_successful_runs"] == 7
    assert s["production_ready_runs_met"] is True
    assert s["production_progress"] == "7/7"


def test_production_progress_below_target(tmp_path, monkeypatch):
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "short"))
    _seed([("succeeded", 25)] * 4)
    s = RunHealthService.summary()
    assert s["consecutive_successful_runs"] == 4
    assert s["production_ready_runs_met"] is False
    assert s["production_progress"] == "4/7"


def test_endpoint_returns_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "ep"))
    _seed([("succeeded", 25), ("insufficient", 0)])
    import json
    from backend.api import run_health

    class Req:
        method = "GET"
        query_params = {}

    resp = run_health(Req())
    body = json.loads(resp.body)
    assert resp.status_code == 200
    assert body["health"] == "healthy" and body["consecutive_successful_runs"] == 2
