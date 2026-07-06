from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import request_payload, safe_int, safe_json_or_error
from backend.reports.reaction_report_service import ReactionReportService
from backend.search.chemical_intelligence_service import ChemicalIntelligenceService

async def structure_search(request: Request) -> Response:
    body = await request_payload(request)
    return safe_json_or_error(lambda: ChemicalIntelligenceService.search_structure(body))


async def reaction_search(request: Request) -> Response:
    body = await request_payload(request)
    return safe_json_or_error(lambda: ChemicalIntelligenceService.search_reaction(body))


async def reaction_name_search(request: Request) -> Response:
    body = await request_payload(request)
    query = str(body.get("query") or request.query_params.get("query") or request.query_params.get("q") or "")
    limit = safe_int(body.get("limit") or request.query_params.get("limit"), 20)
    return safe_json_or_error(lambda: ChemicalIntelligenceService.search_reaction_name({"query": query, "limit": limit}))


async def mechanism_explain(request: Request) -> Response:
    body = await request_payload(request)
    return safe_json_or_error(lambda: ChemicalIntelligenceService.explain_mechanism(body))


async def reaction_report(request: Request) -> Response:
    body = await request_payload(request)
    return safe_json_or_error(lambda: ReactionReportService.generate(body))