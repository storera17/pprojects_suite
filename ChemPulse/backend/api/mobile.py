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

def mobile_summary(_request: Request) -> Response:
    def load() -> dict[str, Any]:
        dashboard = DashboardDataService.dashboard()
        radar = DashboardDataService.publication_radar()
        status = status_or_error()
        return {
            "status": status,
            "kpis": dashboard.get("kpis", {}),
            "publication_radar": radar,
            "publications": DashboardDataService.publications(limit=50),
            "scaffolds": DashboardDataService.top_scaffolds(limit=20),
            "journal_publications": DashboardDataService.journal_publications(),
            "endpoints": {
                "summary": "/api/mobile/summary",
                "import_publications": "/api/publications/import",
                "run_collection": "/api/collection/run",
            },
        }

    return safe_json_or_error(load)


def mobile_app(_request: Request) -> Response:
    return static_response(read_mobile_asset("mobile.html"), "text/html; charset=utf-8")

