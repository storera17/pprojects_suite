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
from frontend.ui.shell import metric_panel, shell_link, status_pill, workspace_shell


def dashboard_page() -> rx.Component:
    search_slot = rx.input(
        placeholder="Search scaffold, journal, DOI, catalyst, transformation...",
        value=AppState.search_query,
        on_change=AppState.set_search_query,
        width="100%",
        class_name="cp-search-shell",
    )
    summary_cards = rx.grid(
        metric_panel(
            "Documents",
            AppState.total_documents.to_string(),
            detail=AppState.dashboard_last_updated_label,
            accent_class="cp-accent-cyan",
            live_id="cp-kpi-documents",
        ),
        metric_panel(
            "Journal Sources",
            AppState.publication_metrics["journal_count"].to_string(),
            detail="Unique literature sources",
            accent_class="cp-accent-green",
            live_id="cp-kpi-journal-sources",
        ),
        metric_panel(
            "Publications",
            AppState.publication_metrics["publication_count"].to_string(),
            detail="Evidence-backed local records",
            accent_class="cp-accent-cyan",
            live_id="cp-kpi-publications",
        ),
        metric_panel(
            "Scaffolds",
            AppState.active_scaffold_count.to_string(),
            detail=AppState.dashboard_data_source,
            accent_class="cp-accent-amber",
            live_id="cp-kpi-scaffolds",
        ),
        columns=rx.breakpoints(initial="1", md="2", lg="4"),
        gap="1rem",
        width="100%",
    )
    freshness_banner = rx.box(
        rx.hstack(
            rx.cond(
                AppState.dashboard_status_tone == "danger",
                status_pill("Unavailable", tone="danger"),
                status_pill("Live local", tone="live"),
            ),
            rx.text(AppState.dashboard_notice, color="var(--cp-text-muted)", font_size="0.9rem"),
            rx.spacer(),
            rx.hstack(
                rx.text("Last refreshed:", class_name="cp-inline-muted"),
                rx.text(AppState.dashboard_last_updated_label, class_name="cp-inline-muted"),
                spacing="1",
                align="center",
            ),
            width="100%",
            align="center",
        ),
        class_name="cp-live-banner",
    )
    dashboard_main = rx.box(
        rx.box(
            galaxy_map(
                AppState.galaxy_figure,
                AppState.selection_summary,
                AppState.handle_galaxy_selection,
                AppState.clear_selection,
            ),
            class_name="cp-grid-span-7",
        ),
        rx.box(
            selection_panel(
                AppState.selection_summary,
                AppState.selected_scaffold,
                AppState.search_query,
                AppState.top_scaffold_label,
                AppState.selected_evidence_count,
                AppState.selected_funding_label,
            ),
            class_name="cp-grid-span-5",
        ),
        rx.box(top10_card("Top Scaffolds by Publications", AppState.top_scaffolds, AppState.select_scaffold), class_name="cp-grid-span-5"),
        rx.box(agent_status_panel(AppState.agent_status, AppState.refresh_agent_status, AppState.run_collection_now, AppState.collection_action_status), class_name="cp-grid-span-7"),
        rx.box(dashboard_graphics(
            AppState.journal_publication_figure,
            AppState.publication_timeline_figure,
            AppState.scaffold_publication_figure,
            AppState.source_diversity_figure,
            AppState.dashboard_summary_cards,
        ), class_name="cp-grid-span-12"),
        rx.box(research_pulse_panel(AppState.research_pulse, AppState.refresh_research_pulse), class_name="cp-grid-span-7"),
        rx.box(funding_card("Journal Publication Sources", AppState.journal_slices), class_name="cp-grid-span-5"),
        rx.box(publication_radar(
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
        ), class_name="cp-grid-span-12"),
        class_name="cp-dashboard-main",
    )
    dashboard_sidebar = rx.box(
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
        manuscript_review_panel(
            AppState.manuscript_review_summary,
            AppState.manuscript_missing_citations,
            AppState.manuscript_requested_experiments,
            AppState.manuscript_journal_transfer_notes,
            AppState.manuscript_response_checklist,
        ),
        predictive_drawer(AppState.predictive_insights, AppState.selected_scaffold, AppState.selection_summary),
        class_name="cp-dashboard-sidebar",
    )
    content = rx.vstack(
        summary_cards,
        freshness_banner,
        rx.box(
            dashboard_main,
            dashboard_sidebar,
            class_name="cp-dashboard-grid",
        ),
        align="stretch",
        spacing="4",
    )
    return workspace_shell(
        active_nav="dashboard",
        brand="ChemPulse",
        title="ChemPulse",
        description="A live local evidence dashboard for chemical discovery, publication intelligence, and predictive context.",
        content=content,
        theme_class=AppState.palette_class,
        search_slot=search_slot,
        topbar_actions=[
            shell_link("ChemPulse OS", "/"),
            shell_link("Chemical Intelligence", "/chemical-intelligence"),
            shell_link("Journal Sentiment", "/journal-sentiment"),
            status_pill("Local data", tone="live"),
            rx.button("Reset", on_click=AppState.reset_dashboard, variant="soft", color_scheme="gray"),
        ],
        status_text="Operational",
        status_tone="live",
    )


