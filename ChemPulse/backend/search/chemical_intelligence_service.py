from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.search.literature_search import search_literature
from backend.search.reaction_mechanism import explain_mechanism, search_reaction, search_reaction_name
from backend.search.structure_matching import search_structure

class ChemicalIntelligenceService:
    search_literature = staticmethod(search_literature)
    search_structure = staticmethod(search_structure)
    search_reaction = staticmethod(search_reaction)
    search_reaction_name = staticmethod(search_reaction_name)
    explain_mechanism = staticmethod(explain_mechanism)

def stable_report_id(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"reaction-report-{digest[:12]}"
