from __future__ import annotations

from backend.data.core_publication_repository import (
    LEGACY_ORPHANED_RUN_MESSAGE,
    ORPHANED_RUN_MESSAGE,
    SUPERSEDED_RUN_MESSAGE,
    CorePublicationRepository,
)
from backend.data.db import get_connection
import backend.data.core_publication_repository as repo_module
from backend.data.payload_repository import PayloadRepository
from backend.services.desktop_status_service import DesktopStatusService
import backend.services.desktop_status_service as desktop_status_module
from backend.services.payload_service import PayloadService
from backend.services.scheduled_collection_service import ScheduledCollectionService
import backend.services.scheduled_collection_service as scheduled_module
import time


class OnePublicationClient:
    def search_works(self, query: str, limit: int, offset: int = 0, entity_type: str = "journal-article", sort: str = "") -> list[dict]:
        if offset:
            return []
        return [
            {
                "id": "scheduled-1",
                "title": "Scheduled scaffold chemistry",
                "doi": "10.1000/scheduled",
                "yearPublished": 2026,
                "authors": [{"name": "Ada Chemist"}],
                "sourceName": "Journal Scheduler",
                "abstract": "A robust scaffold collection run.",
                "topics": ["chemistry", "scaffold"],
            }
        ]


class SecretFailingClient:
    def search_works(self, *args, **kwargs) -> list[dict]:
        raise RuntimeError("CORE failed for token LSlSECRET_DO_NOT_SHOW")


def test_previous_payload_empty_state_is_structured(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    payload = PayloadService.latest_payload()

    assert payload["available"] is False
    assert payload["status"] == "empty"
    assert payload["payload"] == {}
    assert payload["message"]


def test_previous_payload_persists_and_recovers_after_service_restart(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    saved = PayloadService.save_dashboard_payload(
        {"search_query": "glycine", "top_scaffolds": [{"name": "Glycine"}]},
        source="test",
    )
    recovered = PayloadRepository.latest_payload()

    assert saved["available"] is True
    assert recovered["payload_id"] == saved["payload_id"]
    assert recovered["payload"]["search_query"] == "glycine"
    assert recovered["record_count"] == 1


def test_scheduled_collection_reports_missing_api_key_safely(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.delenv("CORE_API_KEY", raising=False)
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: False)
    monkeypatch.setattr(
        scheduled_module,
        "settings_from_env",
        lambda: (_ for _ in ()).throw(RuntimeError("CORE_API_KEY is not set.")),
    )

    result = ScheduledCollectionService.run_now(client=OnePublicationClient())
    status = ScheduledCollectionService.status()

    assert result["status"] == "failed"
    assert status["configured"] is False
    assert status["last_failure_at"] != "Never"
    assert "LSl" not in str(result)


def test_manual_scheduled_collection_writes_database_records(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CORE_API_KEY", "configured-test-key")
    monkeypatch.setenv("CHEMPULSE_CORE_PAGE_SIZE", "1")
    monkeypatch.setenv("CHEMPULSE_TARGET_COUNT", "1")   # M7 adapter target knob
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)

    result = ScheduledCollectionService.run_now(client=OnePublicationClient())
    metrics = CorePublicationRepository.publication_metrics()

    assert result["status"] == "succeeded"
    assert result["inserted"] == 1
    assert metrics["publication_count"] == 1
    assert CorePublicationRepository.recent_publications(query="scheduled")[0]["journal"] == "Journal Scheduler"


def test_failed_collection_persists_redacted_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CORE_API_KEY", "configured-test-key")
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)

    result = ScheduledCollectionService.run_now(client=SecretFailingClient())
    status = ScheduledCollectionService.status()

    assert result["status"] == "failed"
    assert status["last_failure_at"] != "Never"
    assert "LSl" not in status["last_error"]
    assert "SECRET_DO_NOT_SHOW" not in status["last_error"]


def test_manual_scheduled_collection_reports_insufficient_with_diagnostics(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CORE_API_KEY", "configured-test-key")
    monkeypatch.setenv("CHEMPULSE_CORE_PAGE_SIZE", "1")
    monkeypatch.setenv("CHEMPULSE_TARGET_COUNT", "15")   # M7 adapter target knob
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)

    result = ScheduledCollectionService.run_now(client=OnePublicationClient())
    status = ScheduledCollectionService.status()

    assert result["status"] == "insufficient"
    assert result["downloaded"] == 1
    assert result["diagnosis_path"] == "low-yield-query -> insufficient-new-records"
    assert status["last_run_status"] == "insufficient"
    assert status["last_run_downloaded_count"] == 1
    assert status["last_run_inserted_count"] == 1
    assert status["last_run_updated_count"] == 0
    assert status["last_run_diagnosis_path"] == "low-yield-query -> insufficient-new-records"
    assert "required at least 15" in status["last_error"]


def test_successful_latest_run_clears_stale_last_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CORE_API_KEY", "configured-test-key")
    monkeypatch.setenv("CHEMPULSE_CORE_PAGE_SIZE", "1")
    monkeypatch.setenv("CHEMPULSE_TARGET_COUNT", "1")   # M7 adapter target knob
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)

    failed = ScheduledCollectionService.run_now(client=SecretFailingClient())
    recovered = ScheduledCollectionService.run_now(client=OnePublicationClient())
    status = ScheduledCollectionService.status()

    assert failed["status"] == "failed"
    assert recovered["status"] == "succeeded"
    assert status["last_run_status"] == "succeeded"
    assert status["last_error"] == ""


def test_trigger_now_starts_external_collection_without_inline_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    calls: list[dict] = []

    class FakeProcess:
        pid = 4242

        def wait(self):
            return 0

    def fake_popen(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return FakeProcess()

    monkeypatch.setattr(scheduled_module, "_running", False)
    monkeypatch.setattr(scheduled_module.subprocess, "Popen", fake_popen)

    result = ScheduledCollectionService.trigger_now()

    assert result["status"] == "started"
    deadline = time.monotonic() + 3
    while not calls and time.monotonic() < deadline:
        time.sleep(0.01)
    assert calls
    assert calls[0]["env"]["CHEMPULSE_STORAGE_DIR"] == str(tmp_path)


def test_collection_running_marker_survives_process_boundaries(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(scheduled_module, "_running", False)

    scheduled_module._write_collection_marker("running")

    assert ScheduledCollectionService.is_running() is True


def test_finished_collection_marker_is_not_reported_running(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(scheduled_module, "_running", False)

    scheduled_module._write_collection_marker("finished")

    assert ScheduledCollectionService.is_running() is False
    assert not scheduled_module._collection_marker_path().exists()


def test_external_collection_wait_refreshes_running_marker(monkeypatch) -> None:
    calls: list[str] = []

    class FakeProcess:
        def __init__(self) -> None:
            self._polls = 0

        def poll(self):
            self._polls += 1
            return 0 if self._polls > 1 else None

    monkeypatch.setattr(scheduled_module, "_write_collection_marker", lambda status: calls.append(status))
    monkeypatch.setattr(scheduled_module, "_collection_marker_heartbeat_seconds", lambda: 0.001)

    exit_code = scheduled_module._wait_for_external_collection(FakeProcess())

    assert exit_code == 0
    assert calls == ["running"]


def test_packaged_external_collection_uses_bundled_python(tmp_path, monkeypatch) -> None:
    install_root = tmp_path / "ChemPulse"
    runtime_python = install_root / "runtime" / "python.exe"
    runtime_python.parent.mkdir(parents=True)
    runtime_python.write_text("", encoding="utf-8")
    (install_root / "rxconfig.py").write_text("", encoding="utf-8")
    (install_root / "ChemPulse.exe").write_text("", encoding="utf-8")
    storage_dir = tmp_path / "storage"
    calls: list[dict] = []

    class FakeProcess:
        def wait(self):
            return 0

    def fake_popen(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return FakeProcess()

    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(storage_dir))
    monkeypatch.setattr(scheduled_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(scheduled_module.sys, "executable", str(install_root / "ChemPulse.exe"))
    monkeypatch.setattr(scheduled_module.subprocess, "Popen", fake_popen)

    scheduled_module._start_external_collection()

    assert calls
    assert calls[0]["command"][:3] == [str(runtime_python), "-m", "backend.agents.core_publication_agent"]
    assert calls[0]["cwd"] == install_root
    assert calls[0]["env"]["CHEMPULSE_STORAGE_DIR"] == str(storage_dir)
    assert str(install_root) in calls[0]["env"]["PYTHONPATH"]


def test_desktop_status_includes_payload_and_agent_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CORE_API_KEY", "configured-test-key")
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)
    PayloadService.save_dashboard_payload({"recent_publications": [{"core_id": "1"}]}, source="test")

    status = DesktopStatusService.get_status()

    assert status["database_reachable"] is True
    assert status["scaffold_table_available"] is True
    assert status["literature_table_available"] is True
    assert status["previous_payload_available"] is True
    assert status["scheduled_collection_agent"]["configured"] is True
    assert status["desktop_mode"] == "live"


def test_desktop_status_uses_cached_snapshot_while_collection_is_running(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CORE_API_KEY", "configured-test-key")
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)
    PayloadService.save_dashboard_payload({"recent_publications": [{"core_id": "1"}]}, source="test")

    baseline = DesktopStatusService.get_status()
    scheduled_module._write_collection_marker("running")
    monkeypatch.setattr(scheduled_module, "_running", False)
    monkeypatch.setattr(
        desktop_status_module,
        "_database_reachable",
        lambda errors: (_ for _ in ()).throw(AssertionError("database should not be touched while collection owns DuckDB")),
    )
    monkeypatch.setattr(
        desktop_status_module,
        "_scaffold_database_loaded",
        lambda errors: (_ for _ in ()).throw(AssertionError("scaffold probe should not run while collection owns DuckDB")),
    )
    monkeypatch.setattr(
        desktop_status_module,
        "_agent_run_status",
        lambda errors: (_ for _ in ()).throw(AssertionError("run status should come from cache while collection owns DuckDB")),
    )

    status = DesktopStatusService.get_status()

    assert status["scheduled_collection_agent"]["running"] is True
    assert status["previous_payload_available"] == baseline["previous_payload_available"]
    assert "paused to avoid DuckDB file contention" in status["last_connection_error"]


def test_scheduled_collection_status_marks_stale_running_run_failed(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CHEMPULSE_COLLECTION_STALE_MINUTES", "1")
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)
    original_utc_now = repo_module._utc_now
    stale_started_at = original_utc_now() - scheduled_module.timedelta(minutes=2)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: stale_started_at)
    CorePublicationRepository.start_run("stale-running", "chemistry", 1, 1)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: stale_started_at + scheduled_module.timedelta(minutes=2))

    status = ScheduledCollectionService.status()

    assert status["running"] is False
    assert status["last_failure_at"] != "Never"
    assert status["last_error"] == ORPHANED_RUN_MESSAGE
    assert LEGACY_ORPHANED_RUN_MESSAGE not in status["last_error"]
    monkeypatch.setattr(repo_module, "_utc_now", original_utc_now)


def test_superseded_running_run_does_not_count_as_latest_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("CHEMPULSE_COLLECTION_STALE_MINUTES", "1")
    monkeypatch.setattr(scheduled_module, "is_api_key_configured", lambda: True)
    original_utc_now = repo_module._utc_now
    first_started_at = original_utc_now() - scheduled_module.timedelta(minutes=4)
    second_started_at = first_started_at + scheduled_module.timedelta(minutes=2)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: first_started_at)
    CorePublicationRepository.start_run("orphan-running", "chemistry", 1, 1)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: second_started_at)
    CorePublicationRepository.start_run("later-success", "chemistry", 1, 1)
    CorePublicationRepository.finish_run("later-success", "succeeded", 1, 0)
    monkeypatch.setattr(repo_module, "_utc_now", original_utc_now)

    status = ScheduledCollectionService.status()

    assert status["running"] is False
    assert status["last_failure_at"] == "Never"
    assert status["last_success_at"] != "Never"
    with get_connection(read_only=True) as con:
        row = con.execute(
            "SELECT status, error_message FROM core_ingestion_runs WHERE run_id = 'orphan-running'"
        ).fetchone()
    assert row == ("superseded", SUPERSEDED_RUN_MESSAGE)


def test_superseded_run_is_not_visible_latest_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    original_utc_now = repo_module._utc_now
    success_started_at = original_utc_now() - scheduled_module.timedelta(minutes=4)
    newer_started_at = success_started_at + scheduled_module.timedelta(minutes=2)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: success_started_at)
    CorePublicationRepository.start_run("clean-success", "chemistry", 1, 1)
    CorePublicationRepository.finish_run("clean-success", "succeeded", 1, 0)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: newer_started_at)
    CorePublicationRepository.start_run("newer-admin-row", "chemistry", 1, 1)
    CorePublicationRepository.finish_run("newer-admin-row", "superseded", 0, 0, SUPERSEDED_RUN_MESSAGE)
    monkeypatch.setattr(repo_module, "_utc_now", original_utc_now)

    run_status = CorePublicationRepository.agent_run_status()

    assert run_status["latest_run"]["run_id"] == "clean-success"
    assert run_status["latest_run"]["status"] == "succeeded"


def test_legacy_orphan_failure_is_superseded_after_later_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    original_utc_now = repo_module._utc_now
    failed_started_at = original_utc_now() - scheduled_module.timedelta(minutes=4)
    success_started_at = failed_started_at + scheduled_module.timedelta(minutes=2)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: failed_started_at)
    CorePublicationRepository.start_run("legacy-failure", "chemistry", 1, 1)
    CorePublicationRepository.finish_run("legacy-failure", "failed", 0, 0, LEGACY_ORPHANED_RUN_MESSAGE)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: success_started_at)
    CorePublicationRepository.start_run("later-success", "chemistry", 1, 1)
    CorePublicationRepository.finish_run("later-success", "succeeded", 1, 0)
    monkeypatch.setattr(repo_module, "_utc_now", original_utc_now)

    reconciled = CorePublicationRepository.reconcile_orphaned_runs(max_age_hours=1)
    run_status = CorePublicationRepository.agent_run_status()

    assert reconciled["superseded_legacy_failures"] == 1
    assert run_status["last_failure"] is None
    with get_connection(read_only=True) as con:
        row = con.execute(
            "SELECT status, error_message FROM core_ingestion_runs WHERE run_id = 'legacy-failure'"
        ).fetchone()
    assert row == ("superseded", SUPERSEDED_RUN_MESSAGE)


def test_watchdog_orphan_failure_is_superseded_after_later_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    original_utc_now = repo_module._utc_now
    failed_started_at = original_utc_now() - scheduled_module.timedelta(minutes=4)
    success_started_at = failed_started_at + scheduled_module.timedelta(minutes=2)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: failed_started_at)
    CorePublicationRepository.start_run("watchdog-failure", "chemistry", 1, 1)
    CorePublicationRepository.finish_run("watchdog-failure", "failed", 0, 0, ORPHANED_RUN_MESSAGE)
    monkeypatch.setattr(repo_module, "_utc_now", lambda: success_started_at)
    CorePublicationRepository.start_run("later-success", "chemistry", 1, 1)
    CorePublicationRepository.finish_run("later-success", "succeeded", 1, 0)
    monkeypatch.setattr(repo_module, "_utc_now", original_utc_now)

    reconciled = CorePublicationRepository.reconcile_orphaned_runs(max_age_hours=1)
    run_status = CorePublicationRepository.agent_run_status()

    assert reconciled["superseded_legacy_failures"] == 1
    assert run_status["last_failure"] is None
    with get_connection(read_only=True) as con:
        row = con.execute(
            "SELECT status, error_message FROM core_ingestion_runs WHERE run_id = 'watchdog-failure'"
        ).fetchone()
    assert row == ("superseded", SUPERSEDED_RUN_MESSAGE)
