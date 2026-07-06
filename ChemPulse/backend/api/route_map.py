from __future__ import annotations

from backend.api.chemical_intelligence import (
    mechanism_explain,
    reaction_name_search,
    reaction_report,
    reaction_search,
    structure_search,
)
from backend.api.dashboard import (
    dashboard_data,
    dashboard_data_script,
    dashboard_diagnostics,
    documents,
    documents_script,
    galaxy_points,
    galaxy_points_script,
    journal_publications,
    journal_publications_script,
    journals,
    journals_script,
    manuscript_review,
    manuscript_review_script,
    predictive_lab_status,
    predictive_lab_status_script,
    publication_radar,
    publication_radar_script,
    publications,
    publications_script,
    research_pulse,
    research_pulse_script,
    scaffolds,
    scaffolds_script,
    top_scaffolds,
    top_scaffolds_script,
)
from backend.api.mobile import mobile_app, mobile_app_script, mobile_manifest, mobile_service_worker, mobile_summary
from backend.api.publication_routes import import_publications, literature_search
from backend.api.status import (
    desktop_status,
    desktop_status_script,
    run_collection,
    run_collection_script,
    run_health,
    topics_list,
    topics_update,
)

type RouteDefinition = tuple[str, object, list[str]]

def status_routes() -> list[RouteDefinition]:
    return [
        ("/chempulse/api/status", desktop_status, ["GET"]),
        ("/api/status", desktop_status, ["GET"]),
        ("/chempulse/api/collection/run", run_collection, ["POST"]),
        ("/api/collection/run", run_collection, ["POST"]),
        ("/chempulse/api/topics", topics_list, ["GET"]),
        ("/api/topics", topics_list, ["GET"]),
        ("/chempulse/api/topics", topics_update, ["POST"]),
        ("/api/topics", topics_update, ["POST"]),
        ("/chempulse/api/health-summary", run_health, ["GET"]),
        ("/api/health-summary", run_health, ["GET"]),
        ("/chempulse/api/publications/import", import_publications, ["POST"]),
        ("/api/publications/import", import_publications, ["POST"]),
        ("/chempulse/api/mobile/summary", mobile_summary, ["GET"]),
        ("/api/mobile/summary", mobile_summary, ["GET"]),
        ("/chempulse/mobile", mobile_app, ["GET"]),
        ("/mobile", mobile_app, ["GET"]),
        ("/chempulse/mobile/app.js", mobile_app_script, ["GET"]),
        ("/mobile/app.js", mobile_app_script, ["GET"]),
        ("/chempulse/mobile/manifest.webmanifest", mobile_manifest, ["GET"]),
        ("/mobile/manifest.webmanifest", mobile_manifest, ["GET"]),
        ("/chempulse/mobile/service-worker.js", mobile_service_worker, ["GET"]),
        ("/mobile/service-worker.js", mobile_service_worker, ["GET"]),
        ("/chempulse/api/status.js", desktop_status_script, ["GET"]),
        ("/api/status.js", desktop_status_script, ["GET"]),
        ("/chempulse/api/collection/run.js", run_collection_script, ["GET"]),
        ("/api/collection/run.js", run_collection_script, ["GET"]),
    ]
    
def dashboard_routes() -> list[RouteDefinition]:
    return [
        ("/api/documents", documents, ["GET"]),
        ("/api/documents.js", documents_script, ["GET"]),
        ("/api/journals", journals, ["GET"]),
        ("/api/journals.js", journals_script, ["GET"]),
        ("/api/publications", publications, ["GET"]),
        ("/api/publications.js", publications_script, ["GET"]),
        ("/api/scaffolds", scaffolds, ["GET"]),
        ("/api/scaffolds.js", scaffolds_script, ["GET"]),
        ("/api/galaxy/points", galaxy_points, ["GET"]),
        ("/api/galaxy/points.js", galaxy_points_script, ["GET"]),
        ("/api/analytics/top-scaffolds", top_scaffolds, ["GET"]),
        ("/api/analytics/top-scaffolds.js", top_scaffolds_script, ["GET"]),
        ("/api/analytics/journal-publications", journal_publications, ["GET"]),
        ("/api/analytics/journal-publications.js", journal_publications_script, ["GET"]),
        ("/api/research-pulse", research_pulse, ["GET"]),
        ("/api/research-pulse.js", research_pulse_script, ["GET"]),
        ("/api/publication-radar", publication_radar, ["GET"]),
        ("/api/publication-radar.js", publication_radar_script, ["GET"]),
        ("/api/manuscript-review", manuscript_review, ["GET"]),
        ("/api/manuscript-review.js", manuscript_review_script, ["GET"]),
        ("/api/predictive-lab/status", predictive_lab_status, ["GET"]),
        ("/api/predictive-lab/status.js", predictive_lab_status_script, ["GET"]),
        ("/api/dashboard/diagnostics", dashboard_diagnostics, ["GET"]),
        ("/api/dashboard", dashboard_data, ["GET"]),
        ("/api/dashboard.js", dashboard_data_script, ["GET"]),
    ]
    
def chemical_intelligence_routes() -> list[RouteDefinition]:
    return [
        ("/api/search/literature", literature_search, ["GET", "POST"]),
        ("/api/search/structure", structure_search, ["POST"]),
        ("/api/search/reaction", reaction_search, ["POST"]),
        ("/api/search/reaction-name", reaction_name_search, ["GET", "POST"]),
        ("/api/mechanism/explain", mechanism_explain, ["POST"]),
        ("/api/reports/reaction", reaction_report, ["POST"]),
    ]

