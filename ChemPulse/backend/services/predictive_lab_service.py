from __future__ import annotations

from backend.plugins.builtins.frequency_transformer import FrequencyTransformerPlugin
from backend.plugins.registry import PluginRegistry
from backend.services.scaffold_service import ScaffoldService

_registry = PluginRegistry()
_registry.register(FrequencyTransformerPlugin())


class PredictiveLabService:
    @staticmethod
    def _evidence_weighted_predictions(rows: list[dict], focus: str = "") -> list[dict]:
        if not rows:
            return []

        anchor = rows[0]
        scaffold = focus or anchor.get("name", "selected scaffold")
        count = int(anchor.get("count") or 0)
        source = anchor.get("top_funder") or anchor.get("journal_label") or "Unknown source"
        doi = anchor.get("representative_doi", "")
        confidence = min(91, 54 + count * 4)
        support_level = "strong" if count >= 5 else "moderate" if count >= 2 else "limited"
        related = [row.get("name", "") for row in rows[1:3] if row.get("name")]
        related_text = ", ".join(related) if related else "the nearest matched scaffold families"
        return [
            {
                "title": f"{scaffold}: literature-backed analog expansion",
                "reason": (
                    f"{count} matched journal publication(s) support this scaffold in the local corpus. "
                    f"Prioritize analogs that preserve the core and vary substituents one vector at a time."
                ),
                "confidence": f"{confidence}%",
                "evidence_count": count,
                "precedent_count": count,
                "top_funder": source,
                "representative_doi": doi,
                "mechanism": "Frequency-weighted scaffold precedent",
                "lab_action": "Design a 6-12 compound focused library around the retained core.",
                "validation": "Confirm identity/purity by LC-MS and NMR, then compare activity against the nearest cited assay context.",
                "limitation": f"Evidence level is {support_level}; treat this as decision support, not a QSAR endpoint.",
            },
            {
                "title": f"{scaffold}: publication-gap opportunity",
                "reason": (
                    f"Compared with {related_text}, this scaffold has a measurable but not saturated publication footprint. "
                    "That makes it a practical candidate for novelty checks before synthesis."
                ),
                "confidence": f"{max(49, confidence - 9)}%",
                "evidence_count": count,
                "precedent_count": count,
                "top_funder": source,
                "representative_doi": doi,
                "mechanism": "Source diversity and precedent-density heuristic",
                "lab_action": "Run substructure and DOI review before committing expensive reagents.",
                "validation": "Add confirmed internal publications or negative results through manual import to improve ranking.",
                "limitation": "No biological endpoint prediction is made without assay labels or measured response data.",
            },
        ]

    @staticmethod
    def _attach_context(
        insights: list[dict],
        cluster_ids: list[str] | None = None,
        scaffold_name: str = "",
        contextual_rows: list[dict] | None = None,
    ) -> list[dict]:
        contextual_rows = contextual_rows or (
            ScaffoldService.get_top_scaffolds_for_cluster(cluster_ids or [], limit=3)
            if cluster_ids
            else ScaffoldService.get_top_scaffolds(limit=3)
        )
        if scaffold_name:
            contextual_rows = [row for row in contextual_rows if row.get("name") == scaffold_name] or contextual_rows

        if not contextual_rows:
            return []

        anchor = contextual_rows[0]
        realistic = PredictiveLabService._evidence_weighted_predictions(contextual_rows, scaffold_name)
        if realistic:
            return realistic

        enriched: list[dict] = []
        for insight in insights:
            enriched.append(
                {
                    **insight,
                    "evidence_count": insight.get("evidence_count") or anchor.get("count", 0),
                    "precedent_count": insight.get("precedent_count") or insight.get("evidence_count") or anchor.get("count", 0),
                    "top_funder": insight.get("top_funder") or anchor.get("top_funder", ""),
                    "representative_doi": insight.get("representative_doi") or anchor.get("representative_doi", ""),
                }
            )
        return enriched

    @staticmethod
    def get_insights_for_cluster(cluster_ids: list[str]) -> list[dict]:
        return PredictiveLabService._attach_context(_registry.run({"cluster_ids": cluster_ids}), cluster_ids=cluster_ids)

    @staticmethod
    def get_insights_for_scaffold(scaffold_name: str) -> list[dict]:
        return PredictiveLabService._attach_context(_registry.run({"scaffold": scaffold_name}), scaffold_name=scaffold_name)

    @staticmethod
    def get_insights_for_search(query: str) -> list[dict]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        contextual_rows = ScaffoldService.search_scaffolds(cleaned_query, limit=3)
        if not contextual_rows:
            return []

        insights = _registry.run(
            {
                "search_query": cleaned_query,
                "scaffolds": [row.get("name", "") for row in contextual_rows],
            }
        )
        return PredictiveLabService._attach_context(insights, contextual_rows=contextual_rows)

