from __future__ import annotations

from typing import Any
import json

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import javascript_response, safe_dashboard_payload, safe_json_or_error, safe_error
from backend.services.dashboard_data_service import DashboardDataService

