from __future__ import annotations

from backend.services.gmail_publication_lead_service import GmailPublicationLeadService
from backend.services.scheduled_collection_service import ScheduledCollectionService
from backend.services.scaffold_service import ScaffoldService


def import_manual_publication_path(state) -> None:
    from frontend.state import app_state as app_state_module

    if not state.manual_import_path:
        state.manual_import_status = "Add an email link, DOI, article URL, CSV, JSON, JSONL, or folder path first."
        return

    state.loading = True
    try:
        result = app_state_module.import_manual_publications(state.manual_import_path)
        source_label = "quick lead" if result.import_type == "quick" else f"{result.scanned_files} file(s)"
        state.manual_import_status = (
            f"Imported {result.inserted} new / {result.updated} updated "
            f"from {source_label}. Report: {result.report_path}"
        )
        if result.errors:
            state.manual_import_status += f" Warnings: {len(result.errors)}"
        state._refresh_dashboard_view()
        state.refresh_agent_status()
        state.persist_current_payload("desktop-manual-import")
    except Exception as exc:  # noqa: BLE001
        state.manual_import_status = f"Import failed: {exc}"
    finally:
        state.loading = False


def load_gmail_publication_leads(state) -> None:
    state.loading = True
    try:
        result = GmailPublicationLeadService.fetch_recent_academia_recommendations(limit=6)
        state.gmail_recommendation_leads = list(result.get("items", []))
        state.gmail_import_status = (
            f"Loaded {len(state.gmail_recommendation_leads)} Gmail recommendation lead(s) "
            f"from query `{result.get('query', '')}`."
        )
        warnings = list(result.get("warnings", []))
        if warnings:
            state.gmail_import_status += f" Warnings: {len(warnings)}."
    except Exception as exc:  # noqa: BLE001
        state.gmail_recommendation_leads = []
        state.gmail_import_status = f"Gmail lead pull failed: {exc}"
    finally:
        state.loading = False


def import_gmail_publication_lead(state, lead_id: str) -> None:
    from frontend.state import app_state as app_state_module

    selected = next((lead for lead in state.gmail_recommendation_leads if lead.get("lead_id") == lead_id), None)
    if not selected:
        state.manual_import_status = "That Gmail lead is no longer available. Pull Gmail leads again."
        return

    provenance = {
        "channel": "gmail",
        "provider": "Gmail",
        "query": selected.get("query", ""),
        "sender": selected.get("sender", ""),
        "subject": selected.get("subject", ""),
        "received_at": selected.get("received_at", ""),
        "message_id": selected.get("message_id", ""),
        "thread_id": selected.get("thread_id", ""),
        "lead_source": selected.get("lead_source", ""),
    }

    state.loading = True
    try:
        result = app_state_module.import_quick_publication_lead(str(selected.get("lead_source") or ""), provenance=provenance)
        state.manual_import_status = (
            f"Imported {result.inserted} new / {result.updated} updated "
            f"from Gmail: {selected.get('subject') or selected.get('title') or 'Academia recommendation'}. "
            f"Report: {result.report_path}"
        )
        if result.errors:
            state.manual_import_status += f" Warnings: {len(result.errors)}"
        state._refresh_dashboard_view()
        state.refresh_agent_status()
        state.persist_current_payload("desktop-gmail-quick-import")
    except Exception as exc:  # noqa: BLE001
        state.manual_import_status = f"Gmail import failed: {exc}"
    finally:
        state.loading = False


def import_all_gmail_publication_leads(state) -> None:
    from frontend.state import app_state as app_state_module

    if not state.gmail_recommendation_leads:
        state.manual_import_status = "No Gmail recommendation leads are loaded yet. Pull Gmail leads first."
        return

    batch = [
        {
            "raw_source": str(lead.get("lead_source") or ""),
            "provenance": {
                "channel": "gmail",
                "provider": "Gmail",
                "query": lead.get("query", ""),
                "sender": lead.get("sender", ""),
                "subject": lead.get("subject", ""),
                "received_at": lead.get("received_at", ""),
                "message_id": lead.get("message_id", ""),
                "thread_id": lead.get("thread_id", ""),
                "lead_source": lead.get("lead_source", ""),
            },
        }
        for lead in state.gmail_recommendation_leads
    ]

    state.loading = True
    try:
        result = app_state_module.import_quick_publication_leads(batch)
        state.manual_import_status = (
            f"Imported {result.inserted} new / {result.updated} updated from "
            f"{len(state.gmail_recommendation_leads)} Gmail lead(s). Report: {result.report_path}"
        )
        if result.skipped:
            state.manual_import_status += f" Skipped: {result.skipped} duplicate or empty lead(s)."
        if result.errors:
            state.manual_import_status += f" Warnings: {len(result.errors)}"
        state._refresh_dashboard_view()
        state.refresh_agent_status()
        state.persist_current_payload("desktop-gmail-batch-import")
    except Exception as exc:  # noqa: BLE001
        state.manual_import_status = f"Gmail batch import failed: {exc}"
    finally:
        state.loading = False


def add_scaffold_entry(state) -> None:
    result = ScaffoldService.add_scaffold_by_smiles(
        state.scaffold_entry_name,
        state.scaffold_entry_category,
        state.scaffold_entry_family,
        state.scaffold_entry_smiles,
    )
    if not result.get("ok"):
        state.scaffold_entry_status = str(result.get("error", "Could not add scaffold."))
        return

    state.scaffold_entry_status = f"Added {result['name']} as {result['canonical_smiles']}."
    state.scaffold_entry_name = ""
    state.scaffold_entry_category = ""
    state.scaffold_entry_family = ""
    state.scaffold_entry_smiles = ""
    state._refresh_dashboard_view()
    state.persist_current_payload("desktop-scaffold-entry")


def run_collection_now(state) -> None:
    state.collection_action_status = "Running ChemPulse CORE collection..."
    result = ScheduledCollectionService.run_now()
    if result.get("status") == "succeeded":
        state.collection_action_status = (
            f"Collection finished: {result.get('inserted', 0)} new / "
            f"{result.get('updated', 0)} updated."
        )
    elif result.get("status") == "insufficient":
        state.collection_action_status = (
            f"Collection insufficient: {result.get('downloaded', 0)} downloaded / "
            f"{result.get('inserted', 0)} new / {result.get('updated', 0)} updated. "
            f"{result.get('diagnosis_path', '') or result.get('error', '')}"
        ).strip()
    elif result.get("status") == "already_running":
        state.collection_action_status = str(result.get("message"))
    else:
        state.collection_action_status = f"Collection failed: {result.get('error', 'Unknown error')}"
    state._refresh_dashboard_view()
    state.refresh_agent_status()
    state.persist_current_payload("desktop-manual-collection")