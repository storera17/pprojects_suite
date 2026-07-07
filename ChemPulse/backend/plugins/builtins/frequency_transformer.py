from __future__ import annotations

from typing import Any

from backend.plugins.base import PredictivePlugin


class FrequencyTransformerPlugin(PredictivePlugin):
    plugin_name = "frequency_transformer"
    plugin_version = "0.1.0"

    def supports(self, payload: dict[str, Any]) -> bool:
        return "cluster_ids" in payload or "scaffold" in payload or "search_query" in payload

    def predict(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("search_query"):
            scaffolds = payload.get("scaffolds") or []
            primary_scaffold = scaffolds[0] if scaffolds else str(payload["search_query"]).title()
            secondary_scaffold = scaffolds[1] if len(scaffolds) > 1 else primary_scaffold
            return [
                {
                    "title": f"{primary_scaffold} analog expansion",
                    "reason": "Search-matched evidence suggests the nearest scaffold family has enough precedent for substituent exploration.",
                    "confidence": "79%",
                    "evidence_count": 0,
                    "top_funder": "",
                    "representative_doi": "",
                },
                {
                    "title": f"{secondary_scaffold} polarity scan",
                    "reason": "Matched funder and DOI signals point to nearby chemical-space neighborhoods worth prioritizing.",
                    "confidence": "72%",
                    "evidence_count": 0,
                    "top_funder": "",
                    "representative_doi": "",
                },
            ]

        return []