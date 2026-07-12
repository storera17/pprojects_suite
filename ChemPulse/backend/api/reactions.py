from __future__ import annotations

from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import (
    json_response,
    safe_dashboard_payload,
    safe_error,
    safe_int,
    safe_json_or_error,
)
