from __future__ import annotations

import logging
from typing import Any

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem

from backend.chemistry.rdkit_engine import ChemistryEngine
from backend.search.literature_search import search_literature
from backend.search.search_common import metadata, safe_float, safe_int
from backend.services.scaffold_service import ScaffoldService

logger = logging.getLogger(__name__)

_DEFAULT_SIMILARITY_THRESHOLD = 0.35
_MORGAN_RADIUS = 2
_MORGAN_BITS = 2048

