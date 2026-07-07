from __future__ import annotations

from typing import Any

from backend.data.db import ensure_database_exists
from backend.data.repository import GoldRepository
from backend.data.scaffold_registry import ScaffoldRegistry


class ScaffoldService:
    @staticmethod
    def get_top_scaffolds(limit: int = 10) -> list[dict[str, Any]]:
        ensure_database_exists()
        ScaffoldRegistry.ensure_schema_and_seed()
        rows = GoldRepository.top_scaffolds(limit)
        merged = ScaffoldService._merge_registered_scaffolds(rows, limit) if rows else []
        return ScaffoldService._format_scaffold_rows(merged[:limit])

    @staticmethod
    def get_top_scaffolds_for_cluster(cluster_ids: list[str], limit: int = 10) -> list[dict[str, Any]]:
        ensure_database_exists()
        if not cluster_ids:
            return ScaffoldService.get_top_scaffolds(limit)

        rows = GoldRepository.top_scaffolds_for_clusters(cluster_ids, limit)
        return ScaffoldService._format_scaffold_rows(rows)

    @staticmethod
    def search_scaffolds(query: str, limit: int = 10) -> list[dict[str, Any]]:
        ensure_database_exists()
        cleaned_query = query.strip()
        if not cleaned_query:
            return ScaffoldService.get_top_scaffolds(limit)

        rows = GoldRepository.search_scaffolds(cleaned_query, limit)
        registry_rows = ScaffoldService._registered_rows(cleaned_query, limit)
        if rows or registry_rows:
            return ScaffoldService._format_scaffold_rows(ScaffoldService._merge_rows(rows, registry_rows)[:limit])

        return []

    @staticmethod
    def add_scaffold_by_smiles(name: str, category: str, family: str, smiles: str) -> dict[str, Any]:
        ensure_database_exists()
        ScaffoldRegistry.ensure_schema_and_seed()
        return ScaffoldRegistry.add_scaffold_by_smiles(name, category, family, smiles)

    @staticmethod
    def list_registered_scaffolds(limit: int = 1000, query: str = "") -> list[dict[str, Any]]:
        ensure_database_exists()
        return ScaffoldRegistry.list_scaffolds(limit=limit, query=query)

    @staticmethod
    def get_funding_slices() -> list[dict[str, Any]]:
        ensure_database_exists()
        rows = GoldRepository.funding_slices_detailed()
        return [
            {
                "label": row["label"],
                "value": ScaffoldService._format_currency(row["total_funding"]),
                "count": int(row.get("evidence_count") or 0),
                "share": ScaffoldService._format_share(float(row.get("total_funding") or 0.0), rows),
            }
            for row in rows
        ]

    @staticmethod
    def get_funding_slices_for_cluster(cluster_ids: list[str]) -> list[dict[str, Any]]:
        ensure_database_exists()
        if not cluster_ids:
            return ScaffoldService.get_funding_slices()

        rows = GoldRepository.funding_slices_for_clusters(cluster_ids)
        return [
            {
                "label": row["label"],
                "value": ScaffoldService._format_currency(row["total_funding"]),
                "count": int(row.get("evidence_count") or 0),
                "share": ScaffoldService._format_share(float(row.get("total_funding") or 0.0), rows),
            }
            for row in rows
        ]

    @staticmethod
    def get_journal_slices() -> list[dict[str, Any]]:
        ensure_database_exists()
        rows = GoldRepository.journal_publication_slices()
        return ScaffoldService._format_journal_slices(rows)

    @staticmethod
    def get_journal_slices_for_cluster(cluster_ids: list[str]) -> list[dict[str, Any]]:
        ensure_database_exists()
        if not cluster_ids:
            return ScaffoldService.get_journal_slices()

        rows = GoldRepository.journal_publication_slices_for_clusters(cluster_ids)
        return ScaffoldService._format_journal_slices(rows)

    @staticmethod
    def get_overview_metrics() -> dict[str, Any]:
        ensure_database_exists()
        metrics = GoldRepository.overview_metrics()
        return metrics or {"total_documents": 0, "total_funding_usd": 0.0}

    @staticmethod
    def _format_currency(value: float) -> str:
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"${value / 1_000:.1f}K"
        return f"${value:,.0f}"

    @staticmethod
    def _format_scaffold_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        max_count = max((int(row.get("count") or 0) for row in rows), default=1) or 1
        formatted = []
        for index, row in enumerate(rows, start=1):
            count = int(row.get("count") or 0)
            funding = float(row.get("total_funding") or 0.0)
            formatted.append(
                {
                    **row,
                    "rank": index,
                    "count": count,
                    "funding_label": ScaffoldService._format_currency(funding),
                    "publication_label": f"{count} publications",
                    "journal_label": row.get("family") or row.get("top_funder", "Unknown source"),
                    "category": row.get("category", ""),
                    "canonical_smiles": row.get("canonical_smiles", ""),
                    "bar_width": f"{max(8, int((count / max_count) * 100))}%",
                }
            )
        return formatted

    @staticmethod
    def _registered_rows(query: str = "", limit: int = 1000) -> list[dict[str, Any]]:
        return [
            {
                "name": row["name"],
                "count": 0,
                "total_funding": 0.0,
                "top_funder": row["family"],
                "representative_doi": "",
                "category": row["category"],
                "family": row["family"],
                "canonical_smiles": row["canonical_smiles"],
            }
            for row in ScaffoldRegistry.list_scaffolds(limit=limit, query=query)
        ]

    @staticmethod
    def _merge_registered_scaffolds(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
        return ScaffoldService._merge_rows(rows, ScaffoldService._registered_rows(limit=limit * 4))

    @staticmethod
    def _merge_rows(primary: list[dict[str, Any]], secondary: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for row in [*primary, *secondary]:
            name = str(row.get("name") or "")
            if name.lower() == "amino acid":
                continue
            key = name.lower()
            if not key:
                continue
            if key not in merged or int(row.get("count") or 0) > int(merged[key].get("count") or 0):
                merged[key] = row
        return sorted(merged.values(), key=lambda row: (-int(row.get("count") or 0), str(row.get("name") or "")))

    @staticmethod
    def _format_journal_slices(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        total = sum(int(row.get("publication_count") or 0) for row in rows)
        formatted = []
        for row in rows:
            publication_count = int(row.get("publication_count") or 0)
            funding = float(row.get("funding_usd") or 0.0)
            formatted.append(
                {
                    "label": row.get("label") or "Unknown source",
                    "value": f"{publication_count} pubs",
                    "count": int(row.get("scaffold_count") or 0),
                    "publication_count": publication_count,
                    "funding_label": ScaffoldService._format_currency(funding) if funding > 0 else "No funding data",
                    "share": "0%" if total <= 0 else f"{(publication_count / total) * 100:.1f}%",
                }
            )
        return formatted

    @staticmethod
    def _format_share(value: float, rows: list[dict[str, Any]]) -> str:
        total = sum(float(row.get("total_funding") or 0.0) for row in rows)
        if total <= 0:
            return "0%"
        return f"{(value / total) * 100:.1f}%"
