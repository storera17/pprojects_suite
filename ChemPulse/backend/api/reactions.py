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


def reactions_list(request: Request) -> Response:
    from backend.services.reaction_api_service import ReactionApiService

    limit = safe_int(request.query_params.get("limit"), 200)
    return safe_json_or_error(lambda: ReactionApiService.list_reactions(limit=limit))


def reaction_detail(request: Request) -> Response:
    from backend.services.reaction_api_service import ReactionApiService

    reaction_id = request.path_params.get("reaction_id") or request.query_params.get("id") or ""
    try:
        detail = ReactionApiService.reaction_detail(str(reaction_id))
        if detail is None:
            return json_response({"error": "reaction_not_found", "reaction_id": reaction_id}, status_code=404)
        return json_response(safe_dashboard_payload(detail))
    except Exception as exc:  # noqa: BLE001
        return json_response({"error": safe_error(exc), "reaction_id": reaction_id}, status_code=500)
    
    
def model_runs(request: Request) -> Response:
    from backend.services.model_metrics_service import ModelMetricsService

    def load() -> dict[str, Any]:
        runs = ModelMetricsService.runs(limit=safe_int(request.query_params.get("limit"), 50))
        return {"items": runs, "metadata": {"record_count": len(runs), "source": "gold_model_runs"}}

    return safe_json_or_error(load)


def model_metrics(_request: Request) -> Response:
    from backend.services.model_metrics_service import ModelMetricsService

    return safe_json_or_error(ModelMetricsService.dashboard)


def reaction_export(_request: Request) -> Response:
    from backend.reports.reaction_export_service import ReactionExportService

    return safe_json_or_error(ReactionExportService.export)
