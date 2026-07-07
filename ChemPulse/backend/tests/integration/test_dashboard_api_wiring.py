from __future__ import annotations

from starlette.testclient import TestClient

from app import app
from backend.services.dashboard_data_service import DashboardDataService
from frontend.ui.pages.dashboard import dashboard_page


def test_dashboard_section_endpoints_return_stable_shapes() -> None:
    client = TestClient(app._api)
    expectations = {
        "/api/documents": "items",
        "/api/journals": "items",
        "/api/publications": "items",
        "/api/scaffolds": "items",
        "/api/galaxy/points": "points",
        "/api/analytics/top-scaffolds": "items",
        "/api/analytics/journal-publications": "items",
        "/api/research-pulse": "items",
        "/api/publication-radar": "items",
        "/api/predictive-lab/status": "status",
    }

    for route, key in expectations.items():
        response = client.get(route)
        assert response.status_code == 200, route
        payload = response.json()
        assert key in payload, route
        assert "metadata" in payload, route
        assert "record_count" in payload["metadata"], route
        assert "source" in payload["metadata"], route
        assert "last_updated" in payload["metadata"], route
        assert "empty_state_reason" in payload["metadata"], route


def test_dashboard_aggregate_and_diagnostics_cover_all_frontend_sections() -> None:
    client = TestClient(app._api)
    dashboard = client.get("/api/dashboard").json()
    for key in [
        "documents",
        "journals",
        "publications",
        "scaffolds",
        "galaxy",
        "top_scaffolds",
        "journal_publications",
        "research_pulse",
        "publication_radar",
        "predictive_lab",
        "kpis",
    ]:
        assert key in dashboard

    diagnostics = client.get("/api/dashboard/diagnostics").json()
    sections = {item["section"] for item in diagnostics["items"]}
    assert {
        "Documents",
        "Journal sources",
        "Publications",
        "Scaffolds",
        "3D molecular galaxy map",
        "Top scaffolds",
        "Journal publication sources",
        "Research Pulse",
        "Publication Radar",
        "Predictive Lab",
    }.issubset(sections)


def test_dashboard_script_is_available_for_frontend_hydration() -> None:
    client = TestClient(app._api)
    response = client.get("/api/dashboard.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]
    assert "window.ChemPulseDashboard" in response.text
    assert "CORE_API_KEY" not in response.text


def test_mobile_dashboard_routes_are_available() -> None:
    client = TestClient(app._api)

    summary = client.get("/api/mobile/summary")
    mobile = client.get("/mobile")
    script = client.get("/mobile/app.js")
    manifest = client.get("/mobile/manifest.webmanifest")

    assert summary.status_code == 200
    assert "publication_radar" in summary.json()
    assert "status" in summary.json()
    assert mobile.status_code == 200
    assert "ChemPulse Mobile" in mobile.text
    assert script.status_code == 200
    assert "/api/mobile/summary" in script.text
    assert manifest.status_code == 200
    assert manifest.json()["name"] == "ChemPulse Mobile"


def test_dashboard_page_renders_without_browser_side_dashboard_hydration() -> None:
    rendered = str(dashboard_page().render())

    assert "cp-kpi-documents" in rendered
    assert "window.ChemPulseDashboard" not in rendered
    assert "window.ChemPulseAgentStatus" not in rendered
    assert "cp-top-scaffolds-fallback" not in rendered
    assert "cp-journal-sources-fallback" not in rendered
    assert "cp-publication-radar-fallback" not in rendered


def test_dashboard_aggregate_reports_nonzero_kpis_when_services_have_records(monkeypatch) -> None:
    monkeypatch.setattr(
        DashboardDataService,
        "dashboard",
        staticmethod(
            lambda: {
                "documents": {"items": [], "metadata": {"record_count": 45}},
                "journals": {"items": [], "metadata": {"record_count": 16}},
                "publications": {"items": [], "metadata": {"record_count": 540}},
                "scaffolds": {"items": [], "metadata": {"record_count": 45}},
                "galaxy": {"points": [], "metadata": {"record_count": 0}},
                "top_scaffolds": {"items": [], "series": [], "metadata": {"record_count": 10}},
                "journal_publications": {"items": [], "series": [], "metadata": {"record_count": 16}},
                "research_pulse": {"items": [], "metadata": {"record_count": 3}},
                "publication_radar": {"items": [], "journals": [], "metrics": {}, "metadata": {"record_count": 8}},
                "predictive_lab": {"status": {"available": True}, "items": [], "metadata": {"record_count": 1}},
                "kpis": {
                    "documents": 45,
                    "journal_sources": 16,
                    "publications": 540,
                    "scaffolds": 45,
                },
            }
        ),
    )

    client = TestClient(app._api)
    dashboard = client.get("/api/dashboard").json()

    assert dashboard["kpis"]["documents"] > 0
    assert dashboard["kpis"]["journal_sources"] > 0
    assert dashboard["kpis"]["publications"] > 0
    assert dashboard["kpis"]["scaffolds"] > 0
