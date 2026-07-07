from __future__ import annotations

from pathlib import Path

from backend.config import get_config
from app import app
from frontend.desktop import launcher
from backend.services.agent_status_service import AgentStatusService
from backend.services.chemical_space_service import ChemicalSpaceService
from backend.services.desktop_status_service import DesktopStatusService
import backend.services.desktop_status_service as desktop_status_module
from backend.services.scheduled_collection_service import ScheduledCollectionService
from starlette.testclient import TestClient


def test_api_base_url_uses_configured_chempulse_backend_url(monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_API_BASE_URL", "http://127.0.0.1:8123/")

    assert get_config().api_base_url == "http://127.0.0.1:8123"


def test_api_base_url_falls_back_to_reflex_backend_port(monkeypatch) -> None:
    monkeypatch.delenv("CHEMPULSE_API_BASE_URL", raising=False)
    monkeypatch.setenv("BACKEND_PORT", "8124")

    assert get_config().api_base_url == "http://127.0.0.1:8124"


def test_desktop_launcher_exports_chempulse_api_base_url(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeProcess:
        pid = 999999
        returncode = None

        def poll(self):
            return None

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return FakeProcess()

    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.delenv("CHEMPULSE_MOBILE_ACCESS_ENABLED", raising=False)
    monkeypatch.setattr(launcher, "external_python_executable", lambda: "python")
    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)

    launcher.start_reflex(frontend_port=3100, backend_port=8125)

    env = captured["env"]
    assert env["CHEMPULSE_API_BASE_URL"] == "http://127.0.0.1:8125"
    assert env["CHEMPULSE_DEPLOY_URL"] == "http://127.0.0.1:3100"
    assert env["BACKEND_PORT"] == "8125"
    assert env["FRONTEND_PORT"] == "3100"
    assert "--single-port" not in captured["command"]
    assert "--env" in captured["command"]
    assert "dev" in captured["command"]
    assert "--backend-host" in captured["command"]
    assert "127.0.0.1" in captured["command"]


def test_desktop_launcher_prefers_npm_over_bundled_bun_on_windows(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}
    runtime_bun = tmp_path / "runtime" / "bun" / "bin"
    runtime_bun.mkdir(parents=True)
    (runtime_bun / "bun.exe").write_text("", encoding="utf-8")

    class FakeProcess:
        pid = 999997
        returncode = None

        def poll(self):
            return None

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return FakeProcess()

    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.delenv("REFLEX_USE_NPM", raising=False)
    monkeypatch.delenv("REFLEX_BUN_PATH", raising=False)
    monkeypatch.setattr(launcher, "project_root", lambda: tmp_path)
    monkeypatch.setattr(launcher, "external_python_executable", lambda: "python")
    monkeypatch.setattr(launcher.shutil, "which", lambda name, path=None: "C:\\Program Files\\nodejs\\npm.cmd" if name == "npm" else None)
    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)

    launcher.start_reflex(frontend_port=3100, backend_port=8125)

    env = captured["env"]
    assert env["REFLEX_USE_NPM"] == "1"
    assert "REFLEX_BUN_PATH" not in env


def test_desktop_launcher_can_bind_backend_for_mobile_access(monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_MOBILE_ACCESS_ENABLED", "true")

    assert launcher.backend_bind_host() == "0.0.0.0"


def test_desktop_launcher_writes_frontend_env_for_selected_backend(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(launcher, "project_root", lambda: tmp_path)

    launcher.write_frontend_env(frontend_port=3101, backend_port=8126)

    env_path = tmp_path / ".web" / "public" / "env.json"
    env_text = env_path.read_text(encoding="utf-8")
    assert '"PING": "http://127.0.0.1:8126"' in env_text
    assert '"EVENT": "ws://127.0.0.1:8126/_event"' in env_text
    assert '"CHEMPULSE_DEPLOY_URL": "http://127.0.0.1:3101"' in env_text


def test_desktop_launcher_clears_generated_react_router_cache(tmp_path, monkeypatch) -> None:
    generated_dir = tmp_path / ".web" / ".react-router" / "types" / "app" / "routes"
    generated_dir.mkdir(parents=True)
    (generated_dir / "stale.txt").write_text("stale", encoding="utf-8")
    monkeypatch.setattr(launcher, "project_root", lambda: tmp_path)

    launcher.clear_generated_web_state()

    assert not (tmp_path / ".web" / ".react-router").exists()


def test_desktop_launcher_health_check_uses_chempulse_status_route() -> None:
    assert launcher.backend_url(8127) == "http://127.0.0.1:8127/api/status.js"


def test_status_script_aliases_are_available_for_single_port_desktop() -> None:
    client = TestClient(app._api)

    assert client.get("/api/status.js").status_code == 200
    route_paths = {getattr(route, "path", "") for route in app._api.routes}
    assert "/api/collection/run.js" in route_paths


def test_status_route_exposes_insufficient_run_diagnostics(monkeypatch) -> None:
    client = TestClient(app._api)
    monkeypatch.setattr(
        AgentStatusService,
        "get_status",
        staticmethod(
            lambda: {
                "last_database_update": "2026-06-08T12:00:00+00:00",
                "api_agent_available": True,
                "api_key_configured": True,
                "api_key_status": "Configured",
                "api_key_display": "[configured]",
                "agent_wired_to_database": True,
                "agent_wired_to_app": True,
                "latest_run_status": "insufficient",
                "latest_run_query": "chemistry",
                "latest_run_downloaded_count": 1,
                "latest_run_inserted_count": 1,
                "latest_run_updated_count": 0,
                "latest_run_diagnosis_path": "low-yield-query -> insufficient-new-records",
                "latest_run_reason": "Insufficient CORE collection: inserted 1 records; required at least 15.",
                "last_success_time": "2026-06-07T12:00:00+00:00",
                "last_success_records": 25,
                "last_insufficient_time": "2026-06-08T12:00:30+00:00",
                "last_failure_time": "Never",
                "last_failure_error": "",
                "latest_records_processed": 1,
                "backend_reachable": True,
                "database_reachable": True,
                "scaffold_database_loaded": True,
                "chemistry_engine_available": True,
                "active_api_base_url": "http://127.0.0.1:8000",
                "last_connection_error": "",
                "desktop_mode": "live",
                "scaffold_table_available": True,
                "literature_table_available": True,
                "previous_payload_available": False,
                "previous_payload_updated_at": "",
                "previous_payload_record_count": 0,
                "collection_enabled": True,
                "collection_running": False,
                "collection_next_run_at": "2026-06-09T03:15:00",
                "collection_last_run_finished_at": "2026-06-08T12:00:30+00:00",
            }
        ),
    )

    payload = client.get("/api/status").json()

    assert payload["latest_run_status"] == "insufficient"
    assert payload["latest_run_query"] == "chemistry"
    assert payload["latest_run_downloaded_count"] == 1
    assert payload["latest_run_inserted_count"] == 1
    assert payload["latest_run_diagnosis_path"] == "low-yield-query -> insufficient-new-records"
    assert payload["latest_run_reason"].startswith("Insufficient CORE collection")
    assert payload["last_insufficient_time"] == "2026-06-08T12:00:30+00:00"


def test_collection_script_returns_start_result_without_status_lookup(monkeypatch) -> None:
    client = TestClient(app._api)
    monkeypatch.setattr(ScheduledCollectionService, "trigger_now", staticmethod(lambda: {"status": "started", "message": "started"}))
    monkeypatch.setattr(AgentStatusService, "get_status", staticmethod(lambda: (_ for _ in ()).throw(RuntimeError("status should not be fetched"))))

    response = client.get("/api/collection/run.js")

    assert response.status_code == 200
    assert "applyRunResult" in response.text
    assert "started" in response.text


def test_agent_status_panel_uses_reflex_actions_without_browser_polling_script() -> None:
    source = (
        Path(__file__).resolve().parents[3] / "frontend" / "ui" / "components" / "agent_status_panel.py"
    ).read_text(encoding="utf-8")

    assert 'rx.button("Run collection now"' in source
    assert 'rx.button("Refresh"' in source
    assert "window.ChemPulseAgentStatus" not in source


def test_desktop_launcher_releases_stale_chempulse_reflex_process(monkeypatch) -> None:
    calls: list[str] = []

    class FakeAddress:
        port = 8000

    class FakeConnection:
        laddr = FakeAddress()
        status = "LISTEN"
        pid = 123

    class FakeProcess:
        def __init__(self, pid: int) -> None:
            self.pid = pid

        def cmdline(self) -> list[str]:
            return ["python", "-m", "reflex", "run", str(launcher.project_root())]

        def terminate(self) -> None:
            calls.append("terminate")

        def wait(self, timeout: int) -> None:
            calls.append(f"wait:{timeout}")

    fake_psutil = type(
        "FakePsutil",
        (),
        {
            "CONN_LISTEN": "LISTEN",
            "TimeoutExpired": TimeoutError,
            "Error": OSError,
            "net_connections": staticmethod(lambda kind="tcp": [FakeConnection()]),
            "Process": FakeProcess,
        },
    )
    monkeypatch.setattr(launcher, "psutil", fake_psutil)
    monkeypatch.setattr(launcher, "is_port_free", lambda port: False)
    monkeypatch.setattr(launcher, "is_url_ready", lambda url: False)

    launcher.release_stale_reflex_port(8000, "http://localhost:8000/ping")

    assert calls == ["terminate", "wait:8"]


def test_desktop_launcher_starts_fresh_runtime_even_if_old_status_is_ready(monkeypatch) -> None:
    calls: list[str] = []

    class FakeProcess:
        pid = 999998
        returncode = None

        def poll(self):
            return None

    monkeypatch.setattr(launcher, "stop_existing_runtime_processes", lambda: calls.append("stop_existing"))
    monkeypatch.setattr(launcher, "release_stale_reflex_port", lambda *_args: calls.append("release"))
    monkeypatch.setattr(launcher, "clear_generated_web_state", lambda: calls.append("clear_web_state"))
    monkeypatch.setattr(launcher, "find_free_port", lambda port: port)
    monkeypatch.setattr(launcher, "is_url_ready", lambda _url: False)
    monkeypatch.setattr(launcher, "wait_for_url", lambda *_args, **_kwargs: calls.append("wait"))
    monkeypatch.setattr(launcher, "start_reflex", lambda *_args, **_kwargs: FakeProcess())
    monkeypatch.setattr(launcher.webview, "create_window", lambda *_args, **_kwargs: type("Window", (), {"events": type("Events", (), {"closed": type("Closed", (), {"__iadd__": lambda self, handler: self})()})()})())
    monkeypatch.setattr(launcher.webview, "start", lambda *_args, **_kwargs: calls.append("webview"))

    launcher.run_desktop_window()

    assert calls[0] == "stop_existing"
    assert "clear_web_state" in calls
    assert calls.count("wait") == 2


def test_production_chempulse_code_does_not_import_solace() -> None:
    roots = [
        Path(__file__).resolve().parents[3] / "frontend",
        Path(__file__).resolve().parents[3] / "backend",
    ]
    offenders = []
    for root in roots:
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts or "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8").lower()
            if "import solace" in text or "from solace" in text or "solaceruntime" in text:
                offenders.append(str(path))

    assert offenders == []


def test_desktop_status_reports_chempulse_services_without_solace(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(desktop_status_module, "is_api_key_configured", lambda: False)

    status = DesktopStatusService.get_status()

    assert status["database_reachable"] is True
    assert status["scaffold_database_loaded"] is True
    assert status["chemistry_engine_available"] is True
    assert status["desktop_mode"] == "fallback"
    assert "solace" not in str(status).lower()
    assert "provider" not in status
    assert "runtime" not in status


def test_agent_status_surfaces_desktop_diagnostics(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(desktop_status_module, "is_api_key_configured", lambda: False)

    status = AgentStatusService.get_status()

    assert status["backend_reachable"] is True
    assert status["database_reachable"] is True
    assert status["scaffold_database_loaded"] is True
    assert status["chemistry_engine_available"] is True
    assert status["desktop_mode"] == "fallback"
    assert "Solace" not in str(status)


def test_galaxy_points_are_loaded_from_chempulse_scaffold_services(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    points = ChemicalSpaceService.search_galaxy_points("glycine")

    assert points
    assert points[0]["scaffold"] == "Glycine"
    assert points[0]["cluster"].lower() == "amino acid"
