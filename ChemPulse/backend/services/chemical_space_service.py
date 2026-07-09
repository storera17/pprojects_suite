from __future__ import annotations

import hashlib
import math
from typing import Any

import plotly.graph_objects as go

from backend.core.palette_catalog import palette_chart_theme
from backend.data.db import ensure_database_exists
from backend.data.repository import GoldRepository
from backend.data.scaffold_registry import ScaffoldRegistry

class ChemicalSpaceService:
    @staticmethod
    def get_galaxy_points() -> list[dict[str, Any]]:
        ensure_database_exists()
        return GoldRepository.galaxy_points()

    @staticmethod
    def search_galaxy_points(query: str) -> list[dict[str, Any]]:
        ensure_database_exists()
        cleaned_query = query.strip()
        if not cleaned_query:
            return ChemicalSpaceService.get_galaxy_points()

        rows = GoldRepository.search_galaxy_points(cleaned_query)
        if rows:
            return ChemicalSpaceService._append_registered_scaffold_points(rows, cleaned_query)

        registered = ChemicalSpaceService._registered_scaffold_points(cleaned_query)
        if registered:
            return registered

        return []

    @staticmethod
    def _append_registered_scaffold_points(points: list[dict[str, Any]], query: str = "") -> list[dict[str, Any]]:
        existing = {str(point.get("scaffold", "")).lower() for point in points}
        additions = [
            point
            for point in ChemicalSpaceService._registered_scaffold_points(query)
            if str(point.get("scaffold", "")).lower() not in existing
        ]
        return [*points, *additions]

    @staticmethod
    def _registered_scaffold_points(query: str = "") -> list[dict[str, Any]]:
        rows = ScaffoldRegistry.list_scaffolds(limit=1000, query=query)
        points = []
        for index, row in enumerate(rows):
            name = row["name"]
            points.append(
                {
                    "molecule_id": f"registered_{name.lower().replace(' ', '_')}",
                    "id": f"registered_{name.lower().replace(' ', '_')}",
                    "x": None,
                    "y": None,
                    "z": None,
                    "cluster_id": f"registered_{row['category'].lower().replace(' ', '_')}",
                    "cluster": row["category"],
                    "scaffold": name,
                    "funding_usd": 0.0,
                    "evidence_count": 0,
                    "representative_doi": "",
                    "top_funder": row["family"],
                    "molecule_count": 1,
                    "publication_count": 0,
                    "top_topic": row["category"],
                    "canonical_smiles": row["canonical_smiles"],
                    "registry_index": index,
                }
            )
        return points

    @staticmethod
    def _prepared_points(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
        max_evidence = max((int(point.get("evidence_count") or 0) for point in points), default=1) or 1
        prepared: list[dict[str, Any]] = []
        for index, point in enumerate(points):
            scaffold = str(point.get("scaffold") or "Unknown")
            evidence_count = int(point.get("evidence_count") or 0)
            funding = float(point.get("funding_usd") or 0.0)
            x, y, z = ChemicalSpaceService._coordinates(point, scaffold, index, evidence_count, max_evidence, funding)
            prepared.append(
                {
                    **point,
                    "x": x,
                    "y": y,
                    "z": z,
                    "marker_size": 8 + 18 * math.sqrt(max(evidence_count, 1) / max_evidence),
                    "label_text": scaffold,
                    "funding_label": ChemicalSpaceService._format_currency(funding),
                    "publication_label": f"{evidence_count} publications",
                    "evidence_count": evidence_count,
                    "funding_usd": funding,
                    "molecule_count": int(point.get("molecule_count") or 0),
                    "publication_count": int(point.get("publication_count") or evidence_count),
                    "top_topic": point.get("top_topic") or "Scaffold evidence",
                }
            )
        return prepared

    @staticmethod
    def _coordinates(
        point: dict[str, Any],
        scaffold: str,
        index: int,
        evidence_count: int,
        max_evidence: int,
        funding: float,
    ) -> tuple[float, float, float]:
        if point.get("x") is not None and point.get("y") is not None and point.get("z") is not None:
            return float(point["x"]), float(point["y"]), float(point["z"])

        digest = hashlib.sha256(scaffold.encode("utf-8")).digest()
        angle = (int.from_bytes(digest[:2], "big") / 65535) * math.tau
        radius = 0.45 + (index % 7) * 0.09
        evidence_axis = (evidence_count / max(max_evidence, 1)) * 1.4 - 0.7
        funding_axis = min(math.log10(funding + 1) / 8, 1.0) * 1.4 - 0.7
        return round(math.cos(angle) * radius, 4), round(evidence_axis, 4), round(math.sin(angle) * radius + funding_axis * 0.35, 4)

    @staticmethod
    def _format_currency(value: float) -> str:
        if value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"${value / 1_000:.1f}K"
        return f"${value:,.0f}"

    @staticmethod
    def build_galaxy_figure(
        points: list[dict[str, Any]],
        palette_key: str = "default",
        selected_scaffold: str = "", 
        selected_cluster_ids: list[str] | None = None) -> go.Figure:
        theme = palette_chart_theme(palette_key)
        selected_cluster_ids = selected_cluster_ids or []
        if not points:
            fig = go.Figure()
            fig.update_layout(
                margin=dict(l=0, r=0, b=0, t=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            return fig

        prepared_points = ChemicalSpaceService._prepared_points(points)
        has_selection = bool(selected_scaffold or selected_cluster_ids)
        sizes = [
            point["marker_size"] * (1.35 if point.get("scaffold") == selected_scaffold else 1.0)
            for point in prepared_points
        ]

        fig = go.Figure(
            data=[
                go.Scatter3d(
                    x=[point["x"] for point in prepared_points],
                    y=[point["y"] for point in prepared_points],
                    z=[point["z"] for point in prepared_points],
                    mode="markers+text",
                    marker=dict(
                        size=sizes,
                        opacity=0.88 if not has_selection else 0.72,
                        color=[point.get("evidence_count", 0) for point in prepared_points],
                        colorscale=theme["galaxy_scale"],
                        colorbar=dict(title=dict(text="Publications", 
                                                 font=dict(color=theme["text"])), 
                                      tickfont=dict(color=theme["text"])),
                        line=dict(width=1, 
                                  color=theme["galaxy_line"]),
                    ),
                    text=[point.get("label_text", "") for point in prepared_points],
                    textposition="top center",
                    textfont=dict(color=theme["galaxy_label"], 
                                  size=11),
                    customdata=[
                        [
                            point.get("cluster_id", ""),
                            point.get("molecule_id", point.get("id", "")),
                            point.get("scaffold", ""),
                            point.get("representative_doi", ""),
                            point.get("top_funder", ""),
                            point.get("evidence_count", 0),
                            point.get("funding_label", "$0"),
                            point.get("molecule_count", 0),
                            point.get("top_topic", ""),
                            point.get("publication_label", "0 publications"),
                        ]
                        for point in prepared_points
                    ],
                    hovertemplate=(
                        "<b>%{customdata[2]}</b><br>"
                        "Cluster: %{customdata[0]}<br>"
                        "Journal publications: %{customdata[9]}<br>"
                        "Molecule points: %{customdata[7]}<br>"
                        "DOI: %{customdata[3]}<br>"
                        "Top source: %{customdata[4]}<br>"
                        "Funding enrichment: %{customdata[6]}<br>"
                        "Topic: %{customdata[8]}<extra>Click or lasso to inspect</extra>"
                    ),
                )
            ]
        )
        fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode="lasso",
            scene=dict(
                xaxis=dict(visible=False, showbackground=False),
                yaxis=dict(visible=False, showbackground=False),
                zaxis=dict(visible=False, showbackground=False),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        return fig