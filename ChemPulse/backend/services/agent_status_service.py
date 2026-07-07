from __future__ import annotations

from typing import Any

from backend.config import get_config, is_api_key_configured, masked_secret_status
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.db import get_db_path
from backend.services.desktop_status_service import DesktopStatusService
from backend.services.scheduled_collection_service import ScheduledCollectionService

class AgentStatusService:
    @staticmethod
    def get_status() -> dict[str, Any]:
        if ScheduledCollectionService.is_running():
            return _collection_running_status(
                ScheduledCollectionService.status(),
                DesktopStatusService.cached_status(),
            )
        run_status = CorePublicationRepository.agent_run_status()
        api_key_present = is_api_key_configured()
        database_path = get_db_path()
        report_dir = get_config().storage_dir / "reports"
        wired = database_path.exists()
        latest_run = run_status.get("latest_run") or {}
        last_success = run_status.get("last_success") or {}
        last_insufficient = run_status.get("last_insufficient") or {}
        last_failure = run_status.get("last_failure") or {}
        desktop_status = DesktopStatusService.get_status()
        return {
            "last_database_update": _format_dt(run_status.get("last_database_update")),
            "api_agent_available": api_key_present and wired,
            "api_key_configured": api_key_present,
            "api_key_status": "Configured" if api_key_present else "Missing",
            "api_key_display": masked_secret_status(),
            "agent_wired_to_database": wired,
            "agent_wired_to_app": True,
            "database_path": str(database_path),
            "report_dir": str(report_dir),
            "latest_run_status": latest_run.get("status", "never run"),
            "latest_run_query": str(latest_run.get("query") or ""),
            "latest_run_downloaded_count": int(latest_run.get("downloaded_count") or 0),
            "latest_run_inserted_count": int(latest_run.get("inserted_count") or 0),
            "latest_run_updated_count": int(latest_run.get("updated_count") or 0),
            "latest_run_diagnosis_path": str(latest_run.get("diagnosis_path") or ""),
            "latest_run_reason": latest_run.get("error_summary", ""),
            "last_success_time": _format_dt(last_success.get("finished_at")),
            "last_success_records": int(last_success.get("records_processed") or 0),
            "last_insufficient_time": _format_dt(last_insufficient.get("finished_at")),
            "last_failure_time": _format_dt(last_failure.get("finished_at")),
            "last_failure_error": last_failure.get("error_summary", ""),
            "latest_records_processed": int(latest_run.get("records_processed") or 0),
            "desktop_status": desktop_status,
            "backend_reachable": desktop_status["backend_reachable"],
            "database_reachable": desktop_status["database_reachable"],
            "scaffold_database_loaded": desktop_status["scaffold_database_loaded"],
            "chemistry_engine_available": desktop_status["chemistry_engine_available"],
            "active_api_base_url": desktop_status["active_api_base_url"],
            "last_connection_error": desktop_status["last_connection_error"],
            "desktop_mode": desktop_status["desktop_mode"],
            "scaffold_table_available": desktop_status["scaffold_table_available"],
            "literature_table_available": desktop_status["literature_table_available"],
            "previous_payload_available": desktop_status["previous_payload_available"],
            "previous_payload": desktop_status["previous_payload"],
            "previous_payload_updated_at": desktop_status["previous_payload"].get("updated_at", ""),
            "previous_payload_record_count": int(desktop_status["previous_payload"].get("record_count") or 0),
            "scheduled_collection_agent": desktop_status["scheduled_collection_agent"],
            "collection_enabled": bool(desktop_status["scheduled_collection_agent"].get("enabled")),
            "collection_running": bool(desktop_status["scheduled_collection_agent"].get("running")),
            "collection_next_run_at": desktop_status["scheduled_collection_agent"].get("next_run_at", "Never"),
            "collection_last_run_finished_at": desktop_status["scheduled_collection_agent"].get("last_run_finished_at", "Never"),
        }


def _format_dt(value: Any) -> str:
    if not value:
        return "Never"
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _collection_running_status(collection_status: dict[str, Any], desktop_status: dict[str, Any]) -> dict[str, Any]:
    api_key_present = is_api_key_configured()
    database_path = get_db_path()
    return {
        "last_database_update": desktop_status.get("last_database_update", "Refresh pending"),
        "api_agent_available": api_key_present,
        "api_key_configured": api_key_present,
        "api_key_status": "Configured" if api_key_present else "Missing",
        "api_key_display": masked_secret_status(),
        "agent_wired_to_database": database_path.exists(),
        "agent_wired_to_app": True,
        "database_path": str(database_path),
        "report_dir": str(get_config().storage_dir / "reports"),
        "latest_run_status": "running",
        "latest_run_query": str(collection_status.get("last_run_query") or ""),
        "latest_run_downloaded_count": int(collection_status.get("last_run_downloaded_count") or 0),
        "latest_run_inserted_count": int(collection_status.get("last_run_inserted_count") or 0),
        "latest_run_updated_count": int(collection_status.get("last_run_updated_count") or 0),
        "latest_run_diagnosis_path": str(collection_status.get("last_run_diagnosis_path") or ""),
        "latest_run_reason": "",
        "last_success_time": str(collection_status.get("last_success_at") or "Refresh pending"),
        "last_success_records": int(collection_status.get("records_processed") or 0),
        "last_insufficient_time": str(collection_status.get("last_insufficient_at") or "Refresh pending"),
        "last_failure_time": str(collection_status.get("last_failure_at") or "Refresh pending"),
        "last_failure_error": str(collection_status.get("last_error") or ""),
        "latest_records_processed": 0,
        "desktop_status": desktop_status,
        "backend_reachable": bool(desktop_status.get("backend_reachable", True)),
        "database_reachable": bool(desktop_status.get("database_reachable", True)),
        "scaffold_database_loaded": bool(desktop_status.get("scaffold_database_loaded", True)),
        "chemistry_engine_available": bool(desktop_status.get("chemistry_engine_available", True)),
        "active_api_base_url": get_config().api_base_url,
        "last_connection_error": "Collection is running; database status refresh is paused to avoid DuckDB file contention.",
        "desktop_mode": str(desktop_status.get("desktop_mode") or ("live" if api_key_present else "fallback")),
        "scaffold_table_available": bool(desktop_status.get("scaffold_table_available", True)),
        "literature_table_available": bool(desktop_status.get("literature_table_available", True)),
        "previous_payload_available": bool(desktop_status.get("previous_payload_available", False)),
        "previous_payload": desktop_status.get("previous_payload", {}),
        "previous_payload_updated_at": str((desktop_status.get("previous_payload") or {}).get("updated_at", "Refresh pending")),
        "previous_payload_record_count": int((desktop_status.get("previous_payload") or {}).get("record_count") or 0),
        "scheduled_collection_agent": collection_status,
        "collection_enabled": ScheduledCollectionService.enabled(),
        "collection_running": True,
        "collection_next_run_at": str(collection_status.get("next_run_at") or "Refresh pending"),
        "collection_last_run_finished_at": str(collection_status.get("last_run_finished_at") or "Refresh pending"),
    }
