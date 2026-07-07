from __future__ import annotations

from typing import Any

from backend.data.core_publication_repository import CorePublicationRepository


class PublicationIntelligenceService:
    @staticmethod
    def get_metrics() -> dict[str, Any]:
        return CorePublicationRepository.publication_metrics()

    @staticmethod
    def get_recent_publications(limit: int = 6, query: str = "") -> list[dict[str, Any]]:
        return CorePublicationRepository.recent_publications(limit=limit, query=query)

    @staticmethod
    def get_top_journals(limit: int = 5) -> list[dict[str, Any]]:
        return CorePublicationRepository.top_journals(limit=limit)

    @staticmethod
    def get_watchlist(query: str = "") -> list[dict[str, str]]:
        metrics = PublicationIntelligenceService.get_metrics()
        top_journals = PublicationIntelligenceService.get_top_journals(limit=3)

        items = [
            {
                "label": "Corpus",
                "value": f"{metrics.get('publication_count', 0)} publications",
            },
            {
                "label": "Last Sync",
                "value": str(metrics.get("last_run_status", "never run")),
            },
        ]
        if query.strip():
            items.append({"label": "Filter", "value": query.strip()})
        if top_journals:
            items.append({"label": "Top Source", "value": top_journals[0]["label"]})
        return items
