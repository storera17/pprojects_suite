from __future__ import annotations

import reflex as rx

from frontend.state.app_state import AppState
from frontend.ui.components.agent_status_panel import agent_status_panel
from frontend.ui.components.dashboard_graphics import dashboard_graphics
from frontend.ui.components.funding_card import funding_card
from frontend.ui.components.galaxy_map import galaxy_map
from frontend.ui.components.kpi_card import kpi_card
from frontend.ui.components.manuscript_review_panel import manuscript_review_panel
from frontend.ui.components.predictive_drawer import predictive_drawer
from frontend.ui.components.publication_radar import publication_radar
from frontend.ui.components.research_pulse import research_pulse_panel
from frontend.ui.components.selection_panel import selection_panel
from frontend.ui.components.scaffold_entry_panel import scaffold_entry_panel
from frontend.ui.components.top10_card import top10_card


def dashboard_page() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading("ChemPulse", size="8"),
            rx.spacer(),
            rx.input(
                placeholder="Search scaffold, journal, DOI, catalyst, transformation...",
                value=AppState.search_query,
                on_change=AppState.set_search_query,
                width="360px",
                bg="rgba(255,255,255,0.06)",
                border="1px solid rgba(255,255,255,0.10)",
                backdrop_filter="blur(14px)",
            ),
            rx.link("ChemPulse OS", href="/", color="#67E8F9"),
            rx.link("Chemical Intelligence", href="/chemical-intelligence", color="#67E8F9"),
            rx.link("Journal Sentiment", href="/journal-sentiment", color="#67E8F9"),
            rx.button("Reset", on_click=AppState.reset_dashboard, variant="soft", color_scheme="gray"),
            width="100%",
            align="center",
            margin_bottom="0.7rem",
        ),
        rx.box(
            AppState.status_bar_label,
            color="#CBD5E1",
            font_size="0.9rem",
            padding="0.7rem 0.9rem",
            border="1px solid rgba(148,163,184,0.18)",
            background="rgba(15,23,42,0.62)",
            border_radius="8px",
            margin_bottom="1rem",
        ),
        rx.grid(
            kpi_card("Documents", AppState.total_documents.to_string(), "#22d3ee", "cp-kpi-documents"),
            kpi_card("Journal Sources", AppState.publication_metrics["journal_count"].to_string(), "#a855f7", "cp-kpi-journal-sources"),
            kpi_card("Publications", AppState.publication_metrics["publication_count"].to_string(), "#86efac", "cp-kpi-publications"),
            kpi_card("Scaffolds", AppState.active_scaffold_count.to_string(), "#facc15", "cp-kpi-scaffolds"),
            galaxy_map(
                AppState.galaxy_figure,
                AppState.selection_summary,
                AppState.handle_galaxy_selection,
                AppState.clear_selection,
            ),
            selection_panel(
                AppState.selection_summary,
                AppState.selected_scaffold,
                AppState.search_query,
                AppState.top_scaffold_label,
                AppState.selected_evidence_count,
                AppState.selected_funding_label,
            ),
            top10_card("Top Scaffolds by Publications", AppState.top_scaffolds, AppState.select_scaffold),
            agent_status_panel(
                AppState.agent_status,
                AppState.refresh_agent_status,
                AppState.run_collection_now,
                AppState.collection_action_status,
            ),
            scaffold_entry_panel(
                AppState.scaffold_entry_name,
                AppState.scaffold_entry_category,
                AppState.scaffold_entry_family,
                AppState.scaffold_entry_smiles,
                AppState.scaffold_entry_status,
                AppState.set_scaffold_entry_name,
                AppState.set_scaffold_entry_category,
                AppState.set_scaffold_entry_family,
                AppState.set_scaffold_entry_smiles,
                AppState.add_scaffold_entry,
            ),
            funding_card("Journal Publication Sources", AppState.journal_slices),
            dashboard_graphics(
                AppState.journal_publication_figure,
                AppState.publication_timeline_figure,
                AppState.scaffold_publication_figure,
                AppState.source_diversity_figure,
                AppState.dashboard_summary_cards,
            ),
            research_pulse_panel(AppState.research_pulse, AppState.refresh_research_pulse),
            publication_radar(
                AppState.recent_publications,
                AppState.publication_metrics,
                AppState.top_journals,
                AppState.refresh_publication_intelligence,
                AppState.manual_import_path,
                AppState.set_manual_import_path,
                AppState.import_manual_publication_path,
                AppState.manual_import_status,
                AppState.gmail_import_status,
                AppState.gmail_recommendation_leads,
                AppState.load_gmail_publication_leads,
                AppState.import_gmail_publication_lead,
                AppState.import_all_gmail_publication_leads,
            ),
            manuscript_review_panel(
                AppState.manuscript_review_summary,
                AppState.manuscript_missing_citations,
                AppState.manuscript_requested_experiments,
                AppState.manuscript_journal_transfer_notes,
                AppState.manuscript_response_checklist,
            ),
            predictive_drawer(AppState.predictive_insights, AppState.selected_scaffold, AppState.selection_summary),
            columns="repeat(12, 1fr)",
            class_name="dashboard-grid",
            gap="1rem",
            width="100%",
        ),
        padding="2rem",
    )


