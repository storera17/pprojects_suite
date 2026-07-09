from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from backend.core.palette_catalog import palette_chart_theme
from backend.data.db import ensure_database_exists
from backend.data.repository import GoldRepository

class DashboardFigureService:
    @staticmethod
    def journal_publication_figure(limit: int = 12,
                                   palette_key: str = "default") -> go.Figure:
        theme = palette_chart_theme(palette_key)
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
                marker=dict(color=theme["primary"]),
                hovertemplate="<b>%{y}</b><br>Publications: %{x}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig, 
                                              "Journal publication evidence", 
                                              palette_key=palette_key, 
                                              x_title="Publications")

    @staticmethod
    def publication_timeline_figure(palette_key: str = "default") -> go.Figure:
        theme = palette_chart_theme(palette_key)
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
                line=dict(color=theme["secondary"], 
                          width=3),
                marker=dict(size=7, 
                            color=theme["primary"]),
                fill="tozeroy",
                fillcolor=theme["plot_bg"],
                hovertemplate="<b>%{x}</b><br>Publications: %{y}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig,
                                              "Publication timeline", 
                                              palette_key=palette_key,
                                              x_title="Year",
                                              y_title="Publications")
        
    @staticmethod
    def scaffold_publication_figure(limit: int = 12,
                                    palette_key: str = "default"
                                    ) -> go.Figure:
        theme = palette_chart_theme(palette_key)
        try:
            ensure_database_exists()
            rows = GoldRepository.scaffold_journal_breakdown(limit)
        except Exception:
            rows = []
        fig = go.Figure(
            go.Bar(
                x=[row["scaffold"] for row in rows],
                y=[int(row.get("publication_count") or 0) for row in rows],
                marker=dict(color=theme["tertiary"]),
                customdata=[row.get("journal", 
                                    "Unknown source") for row in rows],
                hovertemplate="<b>%{x}</b><br>Publications: %{y}<br>Top source: %{customdata}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig, 
                                              "Scaffold publication rank",
                                              palette_key=palette_key,
                                              y_title="Publications")

    @staticmethod
    def source_diversity_figure(limit: int = 10,
                                palette_key: str = "default") -> go.Figure:
        theme = palette_chart_theme(palette_key)
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
                marker=dict(colors=theme["pie"]),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Scaffolds: %{value}<extra></extra>",
            )
        )
        return DashboardFigureService._layout(fig, 
                                              "Source diversity",
                                              palette_key=palette_key 
                                              show_axes=False)

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
        latest_year = max((int(row.get("year") or 0) for row in year_rows), 
                          default=0)
        funding_rows = [row for row in rows if float(row.get("funding_usd") or 0.0) > 0]
        return [
            {"label": "Journal sources", "value": str(source_count),
             "detail": "distinct publication venues"},
            {"label": "Scaffold-publication links", 
             "value": str(publication_total), 
             "detail": "matched literature evidence"},
            {"label": "Latest publication year", 
             "value": str(latest_year or "n/a"), 
             "detail": "from local corpus"},
            {"label": "Funding-enriched sources", 
             "value": str(len(funding_rows)), 
             "detail": "optional metadata present"},
        ]

    @staticmethod
    def _layout(fig: go.Figure,
                title: str, 
                palette_key: str = "default",
                x_title: str = "",
                y_title: str = "", 
                show_axes: bool = True) -> go.Figure:
        fig.update_layout(
            title=dict(text=title, 
                       font=dict(color=theme["text"],
                                 size=15)),
            margin=dict(l=8,
                        r=8, 
                        b=24,
                        t=42),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=theme["plot_bg"],
            font=dict(color=theme["text"], 
                      size=11),
            showlegend=False,
            height=280,
        )
        if show_axes:
            fig.update_xaxes(title=x_title, 
                             gridcolor=theme["grid"],
                             zeroline=False)
            fig.update_yaxes(title=y_title, 
                             gridcolor=theme["grid"], 
                             zeroline=False, 
                             automargin=True)
        return fig
