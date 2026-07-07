from __future__ import annotations

from typing import Any


def publication_metrics_default() -> dict[str, Any]:
    return {
        "publication_count": 0,
        "journal_count": 0,
        "latest_fetch_at": None,
        "last_run_status": "never run",
        "last_run_delta": "0 new / 0 updated",
        "last_run_error": "",
    }


def manuscript_review_summary_default() -> dict[str, Any]:
    return {
        "manuscript_id": "",
        "title": "",
        "decision": "",
        "source_label": "",
        "report_path": "",
        "citation_count": 0,
        "experiment_count": 0,
        "transfer_count": 0,
        "checklist_count": 0,
    }


def agent_status_default() -> dict[str, Any]:
    return {
        "last_database_update": "Never",
        "api_agent_available": False,
        "api_key_configured": False,
        "api_key_status": "Missing",
        "api_key_display": "Not configured",
        "agent_wired_to_database": False,
        "agent_wired_to_app": True,
        "latest_run_status": "never run",
        "latest_run_query": "",
        "latest_run_downloaded_count": 0,
        "latest_run_inserted_count": 0,
        "latest_run_updated_count": 0,
        "latest_run_diagnosis_path": "",
        "latest_run_reason": "",
        "last_success_time": "Never",
        "last_success_records": 0,
        "last_insufficient_time": "Never",
        "last_failure_time": "Never",
        "last_failure_error": "",
        "latest_records_processed": 0,
        "backend_reachable": False,
        "database_reachable": False,
        "scaffold_database_loaded": False,
        "chemistry_engine_available": False,
        "active_api_base_url": "",
        "last_connection_error": "",
        "desktop_mode": "offline",
        "scaffold_table_available": False,
        "literature_table_available": False,
        "previous_payload_available": False,
        "previous_payload": {},
        "previous_payload_updated_at": "",
        "previous_payload_record_count": 0,
        "scheduled_collection_agent": {
            "configured": False,
            "enabled": False,
            "running": False,
            "last_success_at": "Never",
            "last_insufficient_at": "Never",
            "last_failure_at": "Never",
            "last_run_started_at": "Never",
            "last_run_finished_at": "Never",
            "last_run_status": "never run",
            "last_run_query": "",
            "last_run_downloaded_count": 0,
            "last_run_inserted_count": 0,
            "last_run_updated_count": 0,
            "last_run_diagnosis_path": "",
            "records_processed": 0,
            "last_error": "",
            "next_run_at": "Never",
        },
        "collection_enabled": False,
        "collection_running": False,
        "collection_next_run_at": "Never",
        "collection_last_run_finished_at": "Never",
    }


def previous_payload_default() -> dict[str, Any]:
    return {
        "available": False,
        "payload_id": "",
        "created_at": "",
        "updated_at": "",
        "source": "",
        "status": "empty",
        "record_count": 0,
        "last_error": "",
        "payload": {},
        "message": "No previous ChemPulse payload has been saved yet.",
    }
