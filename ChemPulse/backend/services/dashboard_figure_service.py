from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from backend.data.db import ensure_database_exists
from backend.data.repository import GoldRepository

class DashboardFigureService:
    @staticmethod
    def journal_publication_figure(limit: int = 12) -> go.Figure:
        try:
            ensure_database_exists()
            rows = GoldRepository.journal_publication_slices()[:limit]
        except Exception:
            rows = []
        labels = [row["label"] for row in rows]
        values = [int(row.get("publication_count") or 0) for row in rows]
        fig = go.Figure(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker=dict(color="#22D3EE"),
                hovertemplate="<b>%{y}</b><br>Publications: %{x}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig, "Journal publication evidence", x_title="Publications")

    @staticmethod
    def publication_timeline_figure() -> go.Figure:
        try:
            ensure_database_exists()
            rows = [row for row in GoldRepository.publication_year_counts() if int(row.get("year") or 0) > 1900]
        except Exception:
            rows = []
        rows = rows[-16:]
        fig = go.Figure(
            go.Scatter(
                x=[row["year"] for row in rows],
                y=[row["publication_count"] for row in rows],
                mode="lines+markers",
                line=dict(color="#86EFAC", width=3),
                marker=dict(size=7, color="#FACC15"),
                fill="tozeroy",
                fillcolor="rgba(134,239,172,0.13)",
                hovertemplate="<b>%{x}</b><br>Publications: %{y}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig, "Publication timeline", x_title="Year", y_title="Publications")

    @staticmethod
    def scaffold_publication_figure(limit: int = 12) -> go.Figure:
        try:
            ensure_database_exists()
            rows = GoldRepository.scaffold_journal_breakdown(limit)
        except Exception:
            rows = []
        fig = go.Figure(
            go.Bar(
                x=[row["scaffold"] for row in rows],
                y=[int(row.get("publication_count") or 0) for row in rows],
                marker=dict(color="#A78BFA"),
                customdata=[row.get("journal", "Unknown source") for row in rows],
                hovertemplate="<b>%{x}</b><br>Publications: %{y}<br>Top source: %{customdata}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig, "Scaffold publication rank", y_title="Publications")

    @staticmethod
    def source_diversity_figure(limit: int = 10) -> go.Figure:
        try:
            ensure_database_exists()
            rows = GoldRepository.journal_publication_slices()[:limit]
        except Exception:
            rows = []
        fig = go.Figure(
            go.Pie(
                labels=[row["label"] for row in rows],
                values=[int(row.get("scaffold_count") or 0) for row in rows],
                hole=0.56,
                marker=dict(colors=["#22D3EE", "#86EFAC", "#FACC15", "#A78BFA", "#FB7185", "#38BDF8"]),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Scaffolds: %{value}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig, "Source diversity", show_axes=False)

    @staticmethod
    def summary_cards() -> list[dict[str, Any]]:
        try:
            ensure_database_exists()
            rows = GoldRepository.journal_publication_slices()
            year_rows = GoldRepository.publication_year_counts()
        except Exception:
            rows = []
            year_rows = []
        publication_total = sum(int(row.get("publication_count") or 0) for row in rows)
        source_count = len(rows)
        latest_year = max((int(row.get("year") or 0) for row in year_rows), default=0)
        funding_rows = [row for row in rows if float(row.get("funding_usd") or 0.0) > 0]
        return [
            {"label": "Journal sources", "value": str(source_count), "detail": "distinct publication venues"},
            {"label": "Scaffold-publication links", "value": str(publication_total), "detail": "matched literature evidence"},
            {"label": "Latest publication year", "value": str(latest_year or "n/a"), "detail": "from local corpus"},
            {"label": "Funding-enriched sources", "value": str(len(funding_rows)), "detail": "optional metadata present"},
        ]

    @staticmethod
    def _layout(fig: go.Figure, title: str, x_title: str = "", y_title: str = "", show_axes: bool = True) -> go.Figure:
        fig.update_layout(
            title=dict(text=title, font=dict(color="#E2E8F0", size=15)),
            margin=dict(l=8, r=8, b=24, t=42),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.3)",
            font=dict(color="#CBD5E1", size=11),
            showlegend=False,
            height=280,
        )
        if show_axes:
            fig.update_xaxes(title=x_title, gridcolor="rgba(148,163,184,0.16)", zeroline=False)
            fig.update_yaxes(title=y_title, gridcolor="rgba(148,163,184,0.12)", zeroline=False, automargin=True)
        return fig
