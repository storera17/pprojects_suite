from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import reflex as rx

from backend.core.palette_catalog import DEFAULT_PALETTE_KEY, normalize_palette_key
from backend.data.manual_publication_importer import (
    import_manual_publications,
    import_quick_publication_lead,
    import_quick_publication_leads,
)
from backend.services.chemical_space_service import ChemicalSpaceService
from backend.services.dashboard_figure_service import DashboardFigureService
from frontend.state import app_state_dashboard, app_state_imports, app_state_selection
from frontend.state.app_state_defaults import (
    agent_status_default,
    manuscript_review_summary_default,
    previous_payload_default,
    publication_metrics_default,
)

class AppState(rx.State):
    #Single dashboard view-model for the ChemPulse desktop experience.

    selected_palette: str = rx.LocalStorage(DEFAULT_PALETTE_KEY,
                                            name="chempulse.palette",
                                            sync=True)
    loading: bool = False
    search_query: str = ""
    manual_import_path: str = ""
    manual_import_status: str = ""
    gmail_import_status: str = ""
    gmail_recommendation_leads: list[dict[str, Any]] = []
    collection_action_status: str = ""
    scaffold_entry_name: str = ""
    scaffold_entry_category: str = ""
    scaffold_entry_family: str = ""
    scaffold_entry_smiles: str = ""
    scaffold_entry_status: str = ""

    selected_cluster_ids: list[str] = []
    selected_point_ids: list[str] = []
    selected_evidence_count: int = 0
    selected_funding_total: float = 0.0
    selected_scaffold: str = ""
    selected_molecule_ids: list[str] = []

    total_documents: int = 0
    total_funding_usd: float = 0.0
    active_scaffold_count: int = 0
    top_scaffolds: list[dict[str, Any]] = []
    funding_slices: list[dict[str, Any]] = []
    journal_slices: list[dict[str, Any]] = []
    dashboard_summary_cards: list[dict[str, Any]] = []
    galaxy_points: list[dict[str, Any]] = []
    predictive_insights: list[dict[str, Any]] = []
    research_pulse: list[dict[str, Any]] = []

    publication_metrics: dict[str, Any] = publication_metrics_default()
    recent_publications: list[dict[str, Any]] = []
    top_journals: list[dict[str, Any]] = []

    manuscript_review_summary: dict[str, Any] = manuscript_review_summary_default()
    manuscript_missing_citations: list[dict[str, str]] = []
    manuscript_requested_experiments: list[dict[str, str]] = []
    manuscript_journal_transfer_notes: list[dict[str, str]] = []
    manuscript_response_checklist: list[dict[str, str]] = []

    agent_status: dict[str, Any] = agent_status_default()
    previous_payload: dict[str, Any] = previous_payload_default()

    @rx.event
    def initialize(self):
        app_state_dashboard.initialize(self)

    @rx.event
    def handle_galaxy_selection(self, selection=None):
        app_state_selection.handle_galaxy_selection(self, selection)

    @rx.event
    def clear_selection(self):
        app_state_selection.clear_selection(self)

    @rx.event
    def reset_dashboard(self):
        app_state_selection.reset_dashboard(self)

    @rx.event
    def set_search_query(self, value: str):
        app_state_selection.set_search_query(self, value)

    @rx.event
    def refresh_research_pulse(self):
        app_state_dashboard.refresh_research_pulse(self)

    @rx.event
    def refresh_publication_intelligence(self):
        app_state_dashboard.refresh_publication_intelligence(self)

    @rx.event
    def refresh_manuscript_review(self):
        app_state_dashboard.refresh_manuscript_review(self)

    @rx.event
    def refresh_agent_status(self):
        app_state_dashboard.refresh_agent_status(self)

    @rx.event
    def set_manual_import_path(self, value: str):
        self.manual_import_path = value.strip().strip('"')

    @rx.event
    def import_manual_publication_path(self):
        app_state_imports.import_manual_publication_path(self)

    @rx.event
    def load_gmail_publication_leads(self):
        app_state_imports.load_gmail_publication_leads(self)

    @rx.event
    def import_gmail_publication_lead(self, lead_id: str):
        app_state_imports.import_gmail_publication_lead(self, lead_id)

    @rx.event
    def import_all_gmail_publication_leads(self):
        app_state_imports.import_all_gmail_publication_leads(self)

    @rx.event
    def set_scaffold_entry_name(self, value: str):
        self.scaffold_entry_name = value.strip()

    @rx.event
    def set_scaffold_entry_category(self, value: str):
        self.scaffold_entry_category = value.strip()

    @rx.event
    def set_scaffold_entry_family(self, value: str):
        self.scaffold_entry_family = value.strip()

    @rx.event
    def set_scaffold_entry_smiles(self, value: str):
        self.scaffold_entry_smiles = value.strip()

    @rx.event
    def add_scaffold_entry(self):
        app_state_imports.add_scaffold_entry(self)

    @rx.event
    def select_cluster(self, cluster_ids: list[str]):
        app_state_selection.select_cluster(self, cluster_ids)

    @rx.event
    def select_scaffold(self, scaffold_name: str):
        app_state_selection.select_scaffold(self, scaffold_name)

    @rx.event
    def run_collection_now(self):
        app_state_imports.run_collection_now(self)
        
    @rx.event
    def set_palette(self, value:str):
        self.selected_palette = normalize_palette_key(value)

    @rx.event
    def restore_previous_payload(self):
        app_state_dashboard.restore_previous_payload(self)

    def persist_current_payload(self, source: str):
        app_state_dashboard.persist_current_payload(self, source)

    def _update_selection_totals(self):
        app_state_selection.update_selection_totals(self)

    def _refresh_dashboard_view(self):
        app_state_dashboard.refresh_dashboard_view(self)

    def _load_dashboard_view(self):
        app_state_dashboard.load_dashboard_view(self)

    @rx.var
    def total_funding_label(self) -> str:
        return f"${self.total_funding_usd:,.0f}"

    @rx.var
    def selection_summary(self) -> str:
        if self.selected_scaffold:
            return f"Selected scaffold: {self.selected_scaffold} | {self.selected_evidence_count} journal publications | funding enrichment {self.selected_funding_label}"
        if not self.selected_cluster_ids:
            return "Viewing all clusters"
        if not self.selected_molecule_ids:
            return f"Selected clusters: {', '.join(self.selected_cluster_ids)} | {self.selected_evidence_count} journal publications | funding enrichment {self.selected_funding_label}"
        return f"Selected {len(self.selected_molecule_ids)} points across clusters: {', '.join(self.selected_cluster_ids)}"

    @rx.var
    def selected_funding_label(self) -> str:
        return f"${self.selected_funding_total:,.0f}"

    @rx.var
    def status_bar_label(self) -> str:
        return (
            f"Dataset: Local chemical intelligence layer | {self.active_scaffold_count} scaffolds | "
            f"{self.publication_metrics.get('publication_count', 0)} publications | "
            f"{self.total_documents} scaffold-publication links | {self.total_funding_label} optional funding enrichment | "
            f"{self.selection_summary}"
        )

    @rx.var
    def top_scaffold_label(self) -> str:
        if not self.top_scaffolds:
            return "No scaffold matches"
        leader = self.top_scaffolds[0]
        return f"{leader.get('name', 'Unknown')} ({leader.get('count', 0)} records)"

    @rx.var
    def galaxy_figure(self) -> go.Figure:
        return ChemicalSpaceService.build_galaxy_figure(
            self.galaxy_points,
            selected_scaffold=self.selected_scaffold,
            selected_cluster_ids=self.selected_cluster_ids,
        )

    @rx.var
    def journal_publication_figure(self) -> go.Figure:
        return DashboardFigureService.journal_publication_figure()

    @rx.var
    def publication_timeline_figure(self) -> go.Figure:
        return DashboardFigureService.publication_timeline_figure()

    @rx.var
    def scaffold_publication_figure(self) -> go.Figure:
        return DashboardFigureService.scaffold_publication_figure()

    @rx.var
    def source_diversity_figure(self) -> go.Figure:
        return DashboardFigureService.source_diversity_figure()
