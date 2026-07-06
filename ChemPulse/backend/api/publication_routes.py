from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import json_response, request_payload, safe_int, safe_json_or_error
from backend.data.manual_publication_importer import import_manual_publications
from backend.search.chemical_intelligence_service import ChemicalIntelligenceService