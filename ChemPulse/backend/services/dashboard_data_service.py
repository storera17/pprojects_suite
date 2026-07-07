from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.repository import GoldRepository
from backend.services.manuscript_review_service import ManuscriptReviewService
from backend.services.publication_intelligence_service import PublicationIntelligenceService
from backend.services.research_pulse_service import ResearchPulseService


class DashboardDataService:
    @staticmethod
    def documents() -> dict[str, Any]:
        points = GoldRepository.galaxy_points()
        items = [
            {
                "id": point.get("id") or point.get("molecule_id"),
                "scaffold": point.get("scaffold", "Unknown scaffold"),
                "cluster_id": point.get("cluster_id", ""),
                "publication_count": int(point.get("publication_count") or point.get("evidence_count") or 0),
                "representative_doi": point.get("representative_doi", ""),
            }
            for point in points
        ]
        return _items_response(items, "gold_galaxy_points", "GoldRepository.galaxy_points")

    @staticmethod
    def journals() -> dict[str, Any]:
        items = _format_journal_slices(GoldRepository.journal_publication_slices())
        return _items_response(items, "gold_scaffold_stats", "ScaffoldService.get_journal_slices")

    @staticmethod
    def publications(limit: int = 25) -> dict[str, Any]:
        items = PublicationIntelligenceService.get_recent_publications(limit=limit)
        return _items_response(items, "bronze_core_publications", "PublicationIntelligenceService.get_recent_publications")

    @staticmethod
    def scaffolds(limit: int = 1000) -> dict[str, Any]:
        items = _format_scaffolds(GoldRepository.top_scaffolds(limit=limit))
        return _items_response(items, "gold_scaffold_stats/scaffold_entries", "ScaffoldService.get_top_scaffolds")

    @staticmethod
    def galaxy_points() -> dict[str, Any]:
        points = GoldRepository.galaxy_points()
        return {
            "points": points,
            "metadata": _metadata(
                len(points),
                "gold_galaxy_points/scaffold_entries",
                "ChemicalSpaceService.get_galaxy_points",
            ),
        }

    @staticmethod
    def top_scaffolds(limit: int = 10) -> dict[str, Any]:
        items = _format_scaffolds(GoldRepository.top_scaffolds(limit=limit))
        return {
            "items": items,
            "series": [{"label": item.get("name", ""), "value": int(item.get("count") or 0)} for item in items],
            "metadata": _metadata(len(items), "gold_scaffold_stats", "ScaffoldService.get_top_scaffolds"),
        }

    @staticmethod
    def journal_publications() -> dict[str, Any]:
        items = _format_journal_slices(GoldRepository.journal_publication_slices())
        return {
            "items": items,
            "series": [{"label": item.get("label", ""), "value": int(item.get("publication_count") or 0)} for item in items],
            "metadata": _metadata(len(items), "gold_scaffold_stats", "ScaffoldService.get_journal_slices"),
        }

    @staticmethod
    def research_pulse() -> dict[str, Any]:
        items = ResearchPulseService.get_pulse()
        return _items_response(items, "local_services", "ResearchPulseService.get_pulse")

    @staticmethod
    def publication_radar() -> dict[str, Any]:
        publications = PublicationIntelligenceService.get_recent_publications(limit=8)
        journals = PublicationIntelligenceService.get_top_journals(limit=8)
        metrics = PublicationIntelligenceService.get_metrics()
        return {
            "items": publications,
            "journals": journals,
            "metrics": _json_safe(metrics),
            "metadata": _metadata(
                len(publications),
                "bronze_core_publications/core_ingestion_runs",
                "PublicationIntelligenceService",
            ),
        }

    @staticmethod
    def manuscript_review() -> dict[str, Any]:
        return ManuscriptReviewService.latest_brief()

    @staticmethod
    def predictive_lab_status() -> dict[str, Any]:
        top_scaffolds = _format_scaffolds(GoldRepository.top_scaffolds(limit=1))
        focus = str(top_scaffolds[0].get("name", "")) if top_scaffolds else ""
        insights = [
            {
                "title": f"Evidence-weighted follow-up for {focus}",
                "confidence": "local",
                "reason": f"{top_scaffolds[0].get('publication_label', '0 publications')} support this scaffold context.",
                "lab_action": "Prioritize publication-backed analog search, assay annotation, and scaffold-neighbor comparison.",
                "mechanism": "Local heuristic based on scaffold publication frequency and source diversity.",
                "limitation": "No biological endpoint prediction is made without assay labels or measured response data.",
            }
        ] if focus else []
        status = {
            "available": True,
            "configured": True,
            "selected_scaffold": focus,
            "mode": "evidence-weighted local predictions",
            "message": "Select a scaffold to generate evidence-weighted local prediction suggestions."
            if not insights
            else f"Showing evidence-weighted suggestions for {focus}.",
        }
        return {
            "status": status,
            "items": insights,
            "metadata": _metadata(len(insights), "gold_scaffold_stats", "PredictiveLabService"),
        }

    @staticmethod
    def diagnostics() -> dict[str, Any]:
        sections: list[dict[str, Any]] = []
        checks: list[tuple[str, str, Callable[[], dict[str, Any]], str]] = [
            ("Documents", "/api/documents", DashboardDataService.documents, "gold_galaxy_points"),
            ("Journal sources", "/api/journals", DashboardDataService.journals, "gold_scaffold_stats"),
            ("Publications", "/api/publications", DashboardDataService.publications, "bronze_core_publications"),
            ("Scaffolds", "/api/scaffolds", DashboardDataService.scaffolds, "gold_scaffold_stats/scaffold_entries"),
            ("3D molecular galaxy map", "/api/galaxy/points", DashboardDataService.galaxy_points, "gold_galaxy_points"),
            ("Top scaffolds", "/api/analytics/top-scaffolds", DashboardDataService.top_scaffolds, "gold_scaffold_stats"),
            ("Journal publication sources", "/api/analytics/journal-publications", DashboardDataService.journal_publications, "gold_scaffold_stats"),
            ("Research Pulse", "/api/research-pulse", DashboardDataService.research_pulse, "local_services"),
            ("Publication Radar", "/api/publication-radar", DashboardDataService.publication_radar, "bronze_core_publications"),
            ("Manuscript Review", "/api/manuscript-review", DashboardDataService.manuscript_review, "storage/manuscript-reviews"),
            ("Predictive Lab", "/api/predictive-lab/status", DashboardDataService.predictive_lab_status, "PredictiveLabService"),
        ]
        for name, endpoint, loader, source in checks:
            try:
                payload = loader()
                metadata = payload.get("metadata", {})
                count = int(metadata.get("record_count") or len(payload.get("items", payload.get("points", []))))
                sections.append(
                    {
                        "section": name,
                        "endpoint": endpoint,
                        "reachable": True,
                        "record_count": count,
                        "last_error": "",
                        "last_updated": metadata.get("last_updated", ""),
                        "source": metadata.get("source", source),
                    }
                )
            except Exception as exc:
                sections.append(
                    {
                        "section": name,
                        "endpoint": endpoint,
                        "reachable": False,
                        "record_count": 0,
                        "last_error": _safe_error(exc),
                        "last_updated": _now(),
                        "source": source,
                    }
                )
        return {"items": sections, "metadata": _metadata(len(sections), "diagnostics", "DashboardDataService.diagnostics")}

    @staticmethod
    def dashboard() -> dict[str, Any]:
        metrics = GoldRepository.overview_metrics()
        publication_metrics = PublicationIntelligenceService.get_metrics()
        documents_count = int(metrics.get("total_documents") or len(GoldRepository.galaxy_points()))
        publications_count = int(publication_metrics.get("publication_count") or _publication_count())
        journals_count = int(publication_metrics.get("journal_count") or 0)
        scaffold_count = int((GoldRepository.scaffold_overview_metrics() or {}).get("active_scaffolds") or 0)
        return {
            "documents": {"items": [], "metadata": _metadata(documents_count, "gold_galaxy_points", "GoldRepository.galaxy_points")},
            "journals": {"items": [], "metadata": _metadata(journals_count, "gold_scaffold_stats", "GoldRepository.journal_publication_slices")},
            "publications": {"items": [], "metadata": _metadata(publications_count, "bronze_core_publications", "CorePublicationRepository.publication_metrics")},
            "scaffolds": {"items": [], "metadata": _metadata(scaffold_count, "gold_scaffold_stats", "GoldRepository.scaffold_overview_metrics")},
            "galaxy": {"points": [], "metadata": _metadata(0, "gold_galaxy_points", "Use /api/galaxy/points")},
            "top_scaffolds": {"items": [], "series": [], "metadata": _metadata(0, "gold_scaffold_stats", "Use /api/analytics/top-scaffolds")},
            "journal_publications": {"items": [], "series": [], "metadata": _metadata(0, "gold_scaffold_stats", "Use /api/analytics/journal-publications")},
            "research_pulse": {"items": [], "metadata": _metadata(0, "local_services", "Use /api/research-pulse")},
            "publication_radar": {"items": [], "journals": [], "metrics": publication_metrics, "metadata": _metadata(0, "bronze_core_publications", "Use /api/publication-radar")},
            "manuscript_review": {"items": [], "summary": {}, "metadata": _metadata(0, "storage/manuscript-reviews", "Use /api/manuscript-review")},
            "predictive_lab": {"status": {"available": True}, "items": [], "metadata": _metadata(0, "PredictiveLabService", "Use /api/predictive-lab/status")},
            "kpis": {
                "documents": documents_count,
                "journal_sources": journals_count,
                "publications": publications_count,
                "scaffolds": scaffold_count,
            },
            "metadata": _metadata(10, "dashboard", "DashboardDataService.dashboard"),
        }


def _items_response(items: list[dict[str, Any]], source: str, service: str) -> dict[str, Any]:
    return {"items": _json_safe(items), "metadata": _metadata(len(items), source, service)}


def _format_scaffolds(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    max_count = max((int(row.get("count") or 0) for row in rows), default=1) or 1
    formatted: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        count = int(row.get("count") or 0)
        formatted.append(
            {
                **row,
                "rank": index,
                "count": count,
                "funding_label": _format_currency(float(row.get("total_funding") or 0.0)),
                "publication_label": f"{count} publications",
                "journal_label": row.get("top_funder") or row.get("family") or "Unknown source",
                "bar_width": f"{max(8, int((count / max_count) * 100))}%",
            }
        )
    return formatted


def _format_journal_slices(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = sum(int(row.get("publication_count") or 0) for row in rows)
    return [
        {
            "label": row.get("label") or "Unknown source",
            "value": f"{int(row.get('publication_count') or 0)} pubs",
            "count": int(row.get("scaffold_count") or 0),
            "publication_count": int(row.get("publication_count") or 0),
            "funding_label": _format_currency(float(row.get("funding_usd") or 0.0)) if float(row.get("funding_usd") or 0.0) > 0 else "No funding data",
            "share": "0%" if total <= 0 else f"{(int(row.get('publication_count') or 0) / total) * 100:.1f}%",
        }
        for row in rows
    ]


def _publication_count() -> int:
    return int(CorePublicationRepository.publication_metrics().get("publication_count") or 0)


def _format_currency(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def _metadata(record_count: int, source: str, service: str) -> dict[str, Any]:
    return {
        "record_count": int(record_count),
        "source": source,
        "service": service,
        "last_updated": _now(),
        "empty_state_reason": "" if record_count else "No local ChemPulse records are available for this section yet.",
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_error(exc: Exception) -> str:
    return str(exc).replace("CORE_API_KEY", "literature API key")
