from __future__ import annotations

from typing import Any
import json

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import javascript_response, json_response, request_payload, safe_error, safe_payload
from backend.services.agent_status_service import AgentStatusService
from backend.services.scheduled_collection_service import ScheduledCollectionService