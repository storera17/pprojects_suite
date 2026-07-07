from __future__ import annotations

from frontend.app.factory import create_app
from backend.core import env as env_module
from backend.core.config import get_secret_env
from frontend.ui.pages.chemical_intelligence import chemical_intelligence_page


def test_app_factory_registers_expected_pages_and_routes() -> None:
    app = create_app()

    route_paths = {getattr(route, "path", "") for route in app._api.routes}

    assert "/api/status" in route_paths
    assert "/api/dashboard" in route_paths
    assert "/api/search/literature" in route_paths
    assert "/mobile" in route_paths


def test_project_env_value_is_loaded_when_process_env_is_missing(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text("CORE_API_KEY=project-file-key\n", encoding="utf-8")
    monkeypatch.delenv("CORE_API_KEY", raising=False)
    monkeypatch.setattr(env_module, "project_root", lambda: tmp_path)
    monkeypatch.setattr(env_module, "_windows_user_env", lambda _name: "")

    assert get_secret_env("CORE_API_KEY") == "project-file-key"


def test_process_env_overrides_project_env(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text("CORE_API_KEY=project-file-key\n", encoding="utf-8")
    monkeypatch.setenv("CORE_API_KEY", "process-env-key")
    monkeypatch.setattr(env_module, "project_root", lambda: tmp_path)
    monkeypatch.setattr(env_module, "_windows_user_env", lambda _name: "")

    assert get_secret_env("CORE_API_KEY") == "process-env-key"


def test_chemical_intelligence_page_loads_packaged_assets() -> None:
    rendered = str(chemical_intelligence_page().render())

    assert "cp-ci-root" in rendered
    assert "Topic Search" in rendered
    assert "window.ChemPulseChemicalIntelligence" in rendered