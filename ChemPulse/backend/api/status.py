from __future__ import annotations

from typing import Any
import json

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import javascript_response, json_response, request_payload, safe_error, safe_payload
from backend.services.agent_status_service import AgentStatusService
from backend.services.scheduled_collection_service import ScheduledCollectionService

def desktop_status(_request: Request) -> Response:
    return json_response(status_or_error())

def run_collection(_request: Request) -> Response:
    result = ScheduledCollectionService.trigger_now()
    return json_response(safe_payload(result), status_code=200 if result.get("status") != "failed" else 503)

def desktop_status_script(_request: Request) -> Response:
    payload = json.dumps(status_or_error(), allow_nan=False)
    return javascript_response(f"window.ChemPulseAgentStatus&&window.ChemPulseAgentStatus.applyStatus({payload});")

def run_collection_script(_request: Request) -> Response:
    result = safe_payload(ScheduledCollectionService.trigger_now())
    payload = json.dumps(result, allow_nan=False)
    return javascript_response(
        "window.ChemPulseAgentStatus&&"
        f"window.ChemPulseAgentStatus.applyRunResult({payload});"
        "window.ChemPulseAgentStatus&&"
        "window.setTimeout(function(){window.ChemPulseAgentStatus.refresh();},1500);"
    )

def run_health(_request: Request) -> Response:
    from backend.services.run_health_service import RunHealthService

    try:
        return json_response(RunHealthService.summary())
    except Exception as exc:  # noqa: BLE001
        return json_response({"health": "unknown", "error": safe_error(exc)}, status_code=500)

def topics_list(_request: Request) -> Response:
    from backend.services import topics_service

    try:
        topics_service.ensure_seeded()
        return json_response({"topics": topics_service.list_topics()})
    except Exception as exc:  # noqa: BLE001
        return json_response({"topics": [], "error": safe_error(exc)}, status_code=500)

async def topics_update(request: Request) -> Response:
    from backend.services import topics_service

    body = await request_payload(request)
    try:
        result = topics_service.update_from_command_center(body)
        return json_response(result, status_code=200 if result.get("ok") else 400)
    except Exception as exc:  # noqa: BLE001
        return json_response({"ok": False, "topics": [], "errors": [safe_error(exc)]}, status_code=500)

def status_or_error() -> dict[str, Any]:
    try:
        return public_status(AgentStatusService.get_status())
    except Exception as exc:  # noqa: BLE001
        return safe_payload(
            {
                "last_database_update": "Never",
                "api_agent_available": False,
                "api_key_configured": False,
                "api_key_status": "Unknown",
                "api_key_display": "Unknown",
                "agent_wired_to_database": False,
                "agent_wired_to_app": True,
                "latest_run_status": "status error",
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
                "last_connection_error": f"ChemPulse status unavailable: {exc}",
                "desktop_mode": "offline",
                "scaffold_table_available": False,
                "literature_table_available": False,
                "previous_payload_available": False,
                "previous_payload_updated_at": "",
                "previous_payload_record_count": 0,
                "collection_enabled": False,
                "collection_running": False,
                "collection_next_run_at": "Never",
                "collection_last_run_finished_at": "Never",
            }
        )
