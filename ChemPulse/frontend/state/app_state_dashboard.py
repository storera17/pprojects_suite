from __future__ import annotations

import logging

from backend.data.db import ensure_database_exists
from backend.services.agent_status_service import AgentStatusService
from backend.services.chemical_space_service import ChemicalSpaceService
from backend.services.dashboard_figure_service import DashboardFigureService
from backend.services.manuscript_review_service import ManuscriptReviewService
from backend.services.payload_service import PayloadService
from backend.services.predictive_lab_service import PredictiveLabService
from backend.services.publication_intelligence_service import PublicationIntelligenceService
from backend.services.research_pulse_service import ResearchPulseService
from backend.services.scheduled_collection_service import ScheduledCollectionService
from backend.services.scaffold_service import ScaffoldService

logger = logging.getLogger(__name__)


def initialize(state) -> None:
    state.loading = True
    state.collection_action_status = ""
    try:
        ScheduledCollectionService.register_once()
        state.previous_payload = PayloadService.latest_payload()
        ensure_database_exists()
        refresh_dashboard_view(state)
        persist_current_payload(state, "desktop-initialize")
        state.collection_action_status = ""
    except Exception as exc:  # noqa: BLE001
        state.collection_action_status = f"ChemPulse local data is temporarily unavailable: {exc}"
    refresh_agent_status(state)
    state.loading = False


def refresh_research_pulse(state) -> None:
    state.research_pulse = ResearchPulseService.get_pulse(
        cluster_ids=state.selected_cluster_ids,
        scaffold_name=state.selected_scaffold,
        search_query=state.search_query,
    )


def refresh_publication_intelligence(state) -> None:
    state.publication_metrics = PublicationIntelligenceService.get_metrics()
    state.recent_publications = PublicationIntelligenceService.get_recent_publications(
        limit=6,
        query=state.search_query,
    )
    state.top_journals = PublicationIntelligenceService.get_top_journals(limit=5)


def refresh_manuscript_review(state) -> None:
    review = ManuscriptReviewService.latest_brief()
    state.manuscript_review_summary = review["summary"]
    state.manuscript_missing_citations = review["missing_citations"]
    state.manuscript_requested_experiments = review["requested_experiments"]
    state.manuscript_journal_transfer_notes = review["journal_transfer_notes"]
    state.manuscript_response_checklist = review["response_checklist"]


def refresh_agent_status(state) -> None:
    state.agent_status = AgentStatusService.get_status()


def restore_previous_payload(state) -> None:
    state.previous_payload = PayloadService.latest_payload()


def persist_current_payload(state, source: str) -> None:
    payload = {
        "search_query": state.search_query,
        "selected_cluster_ids": state.selected_cluster_ids,
        "selected_scaffold": state.selected_scaffold,
        "selected_molecule_ids": state.selected_molecule_ids,
        "total_documents": state.total_documents,
        "active_scaffold_count": state.active_scaffold_count,
        "publication_metrics": state.publication_metrics,
        "top_scaffolds": state.top_scaffolds,
        "galaxy_points": state.galaxy_points,
        "recent_publications": state.recent_publications,
        "research_pulse": state.research_pulse,
    }
    state.previous_payload = PayloadService.save_dashboard_payload(payload, source=source)
    state.agent_status = {
        **state.agent_status,
        "previous_payload_available": bool(state.previous_payload.get("available")),
        "previous_payload": state.previous_payload,
        "previous_payload_updated_at": str(state.previous_payload.get("updated_at") or ""),
        "previous_payload_record_count": int(state.previous_payload.get("record_count") or 0),
    }


def refresh_dashboard_view(state) -> None:
    try:
        load_dashboard_view(state)
        state.collection_action_status = ""
    except Exception as exc:  # noqa: BLE001
        logger.exception("Dashboard refresh failed")
        state.collection_action_status = f"ChemPulse local data is temporarily unavailable: {exc}"


def load_dashboard_view(state) -> None:
    metrics = ScaffoldService.get_overview_metrics()
    state.total_documents = int(metrics.get("total_documents", 0))
    state.total_funding_usd = float(metrics.get("total_funding_usd", 0.0))
    state.active_scaffold_count = len(ScaffoldService.get_top_scaffolds(limit=1000))
    state.dashboard_summary_cards = DashboardFigureService.summary_cards()
    state.galaxy_points = (
        ChemicalSpaceService.search_galaxy_points(state.search_query)
        if state.search_query
        else ChemicalSpaceService.get_galaxy_points()
    )

    if state.selected_cluster_ids:
        state.top_scaffolds = ScaffoldService.get_top_scaffolds_for_cluster(state.selected_cluster_ids, limit=10)
        state.funding_slices = ScaffoldService.get_funding_slices_for_cluster(state.selected_cluster_ids)
        state.journal_slices = ScaffoldService.get_journal_slices_for_cluster(state.selected_cluster_ids)
        state.predictive_insights = PredictiveLabService.get_insights_for_cluster(state.selected_cluster_ids)
        state.research_pulse = ResearchPulseService.get_pulse(
            cluster_ids=state.selected_cluster_ids,
            search_query=state.search_query,
        )
    else:
        state.top_scaffolds = (
            ScaffoldService.search_scaffolds(state.search_query, limit=10)
            if state.search_query
            else ScaffoldService.get_top_scaffolds(limit=10)
        )
        state.funding_slices = ScaffoldService.get_funding_slices()
        state.journal_slices = ScaffoldService.get_journal_slices()
        if state.selected_scaffold:
            state.predictive_insights = PredictiveLabService.get_insights_for_scaffold(state.selected_scaffold)
            state.research_pulse = ResearchPulseService.get_pulse(
                scaffold_name=state.selected_scaffold,
                search_query=state.search_query,
            )
        else:
            state.predictive_insights = (
                PredictiveLabService.get_insights_for_search(state.search_query) if state.search_query else []
            )
            state.research_pulse = ResearchPulseService.get_pulse(search_query=state.search_query)

    state._update_selection_totals()
    refresh_publication_intelligence(state)
    refresh_manuscript_review(state)
