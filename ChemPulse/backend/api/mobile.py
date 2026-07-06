from __future__ import annotations

from typing import Any
import json

from starlette.requests import Request
from starlette.responses import Response

from backend.api.dashboard import dashboard_data
from backend.api.mobile_assets import read_mobile_asset
from backend.api.responses import json_response, safe_json_or_error, static_headers, static_response
from backend.api.status import status_or_error
from backend.services.dashboard_data_service import DashboardDataService
