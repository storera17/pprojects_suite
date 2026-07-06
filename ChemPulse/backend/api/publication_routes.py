from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import json_response, request_payload, safe_int, safe_json_or_error
from backend.data.manual_publication_importer import import_manual_publications
from backend.search.chemical_intelligence_service import ChemicalIntelligenceService

async def literature_search(request: Request) -> Response:
    body = await request_payload(request)
    query = str(body.get("query") or request.query_params.get("query") or request.query_params.get("q") or "")
    limit = safe_int(body.get("limit") or request.query_params.get("limit"), 25)
    return safe_json_or_error(lambda: ChemicalIntelligenceService.search_literature(query=query, limit=limit))


async def import_publications(request: Request) -> Response:
    body = await request_payload(request)
    source = str(body.get("source") or body.get("path") or body.get("url") or body.get("doi") or "").strip()
    recursive = bool(body.get("recursive", True))
    if not source:
        return json_response(
            {"ok": False, "error": "Add a DOI, article URL, CSV, JSON, JSONL, or folder path first."},
            status_code=400,
        )
    return safe_json_or_error(lambda: {"ok": True, **import_manual_publications(source, recursive=recursive).as_dict()})
