from __future__ import annotations

from typing import Any

from backend.services.scaffold_service import ScaffoldService


class ResearchPulseService:
    """Build concise dashboard signals from the same repository-backed facts."""

    @staticmethod
    def get_pulse(
        cluster_ids: list[str] | None = None,
        scaffold_name: str = "",
        search_query: str = "",
    ) -> list[dict[str, Any]]:
        cluster_ids = cluster_ids or []
        if scaffold_name:
            scaffold_rows = [row for row in ScaffoldService.get_top_scaffolds(limit=10) if row.get("name") == scaffold_name]
            scope = "Scaffold focus"
        elif cluster_ids:
            scaffold_rows = ScaffoldService.get_top_scaffolds_for_cluster(cluster_ids, limit=3)
            scope = "Cluster selection"
        elif search_query.strip():
            scaffold_rows = ScaffoldService.search_scaffolds(search_query, limit=3)
            scope = "Search focus"
        else:
            scaffold_rows = ScaffoldService.get_top_scaffolds(limit=3)
            scope = "Global overview"

        funding_rows = (
            ScaffoldService.get_funding_slices_for_cluster(cluster_ids)
            if cluster_ids
            else ScaffoldService.get_funding_slices()
        )

        pulses: list[dict[str, Any]] = []
        if scaffold_rows:
            leader = scaffold_rows[0]
            pulses.append(
                {
                    "tag": scope,
                    "title": f"{leader.get('name', 'Unknown scaffold')} leads {scope.lower()}",
                    "body": (
                        f"{leader.get('count', 0)} evidence records and "
                        f"{leader.get('funding_label', '$0')} tracked funding support this context."
                    ),
                    "metric": str(leader.get("top_funder") or "No funder"),
                }
            )

        if funding_rows:
            funder = funding_rows[0]
            pulses.append(
                {
                    "tag": "Funding",
                    "title": f"{funder.get('label', 'Unknown')} is the strongest funding signal",
                    "body": "Use this slice to prioritize literature triage and sponsor-aware discovery paths.",
                    "metric": str(funder.get("value", "$0")),
                }
            )

        pulses.append(
            {
                "tag": "Workflow",
                "title": "Predictive Lab is ready for the current context",
                "body": "Select a galaxy cluster or scaffold to refresh local predictions with evidence-backed context.",
                "metric": "Live",
            }
        )
        return pulses

