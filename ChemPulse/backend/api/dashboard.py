from __future__ import annotations

from typing import Any
import json

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import javascript_response, safe_dashboard_payload, safe_json_or_error, safe_error
from backend.services.dashboard_data_service import DashboardDataService

def documents(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.documents)


def journals(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.journals)


def publications(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.publications)


def scaffolds(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.scaffolds)


def galaxy_points(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.galaxy_points)


def top_scaffolds(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.top_scaffolds)


def journal_publications(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.journal_publications)


def research_pulse(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.research_pulse)


def publication_radar(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.publication_radar)


def manuscript_review(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.manuscript_review)


def predictive_lab_status(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.predictive_lab_status)


def dashboard_diagnostics(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.diagnostics)


def dashboard_data(_request: Request) -> Response:
    return safe_json_or_error(DashboardDataService.dashboard)


def dashboard_data_script(_request: Request) -> Response:
    return javascript_response(
        """
(function(){
  if (!window.ChemPulseDashboard) return;
  var origin = new URL(document.currentScript.src).origin;
  [
    "/api/documents.js",
    "/api/journals.js",
    "/api/publications.js",
    "/api/scaffolds.js",
    "/api/galaxy/points.js",
    "/api/analytics/top-scaffolds.js",
    "/api/analytics/journal-publications.js",
    "/api/research-pulse.js",
    "/api/publication-radar.js",
    "/api/manuscript-review.js",
    "/api/predictive-lab/status.js"
  ].reduce(function(chain, path){
    return chain.then(function(){
      return new Promise(function(resolve){
        var script = document.createElement("script");
        script.src = origin + path + "?t=" + Date.now();
        script.async = false;
        script.onload = resolve;
        script.onerror = resolve;
        document.head.appendChild(script);
      });
    });
  }, Promise.resolve());
})();
""".strip()
    )


def documents_script(_request: Request) -> Response:
    return dashboard_patch_script("documents", DashboardDataService.documents)


def journals_script(_request: Request) -> Response:
    return dashboard_patch_script("journals", DashboardDataService.journals)


def publications_script(_request: Request) -> Response:
    return dashboard_patch_script("publications", DashboardDataService.publications)


def scaffolds_script(_request: Request) -> Response:
    return dashboard_patch_script("scaffolds", DashboardDataService.scaffolds)


def galaxy_points_script(_request: Request) -> Response:
    return dashboard_patch_script("galaxy", DashboardDataService.galaxy_points, "points")


def top_scaffolds_script(_request: Request) -> Response:
    return dashboard_patch_script("top_scaffolds", DashboardDataService.top_scaffolds)


def journal_publications_script(_request: Request) -> Response:
    return dashboard_patch_script("journal_publications", DashboardDataService.journal_publications)


def research_pulse_script(_request: Request) -> Response:
    return dashboard_patch_script("research_pulse", DashboardDataService.research_pulse)


def publication_radar_script(_request: Request) -> Response:
    return dashboard_patch_script("publication_radar", DashboardDataService.publication_radar)


def manuscript_review_script(_request: Request) -> Response:
    return dashboard_patch_script("manuscript_review", DashboardDataService.manuscript_review)


def predictive_lab_status_script(_request: Request) -> Response:
    return dashboard_patch_script("predictive_lab", DashboardDataService.predictive_lab_status, "status")


def dashboard_patch_script(key: str, loader, primary_key: str = "items") -> Response:
    payload = json.dumps(dashboard_section(loader, primary_key), allow_nan=False)
    safe_key = json.dumps(key)
    return javascript_response(f"window.ChemPulseDashboard&&window.ChemPulseDashboard.applyPatch({safe_key},{payload});")


def dashboard_section(loader, primary_key: str = "items") -> dict[str, Any]:
    try:
        return safe_dashboard_payload(loader())
    except Exception as exc:  # noqa: BLE001
        return {
            primary_key: [] if primary_key != "status" else {},
            "items": [],
            "metadata": {
                "record_count": 0,
                "source": "error",
                "last_updated": "",
                "empty_state_reason": f"ChemPulse data unavailable: {safe_error(exc)}",
                "last_error": safe_error(exc),
            },
        }