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

