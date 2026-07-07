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

def parse_structure(value: str) -> tuple[Any | None, str | None, str | None]:
    """Parse a SMILES or MolBlock string. Returns (mol, canonical_smiles, error)."""
    raw_value = str(value or "")
    if not raw_value.strip():
        return None, None, "Structure input is required."
    try:
        if "\n" in raw_value and "M  END" in raw_value:
            mol = Chem.MolFromMolBlock(raw_value.rstrip(), sanitize=True)
        else:
            mol = Chem.MolFromSmiles(raw_value.strip())
    except Exception:
        logger.warning("RDKit raised while parsing structure input", exc_info=True)
        return None, None, "Invalid structure. Use a valid SMILES or MolBlock."
    if mol is None:
        return None, None, "Invalid structure. Use a valid SMILES or MolBlock."
    try:
        Chem.SanitizeMol(mol)
    except Exception:
        logger.info("Structure failed sanitization: %r", raw_value)
        return None, None, "Invalid structure. Check valence, aromaticity, and atom syntax."
    canonical, error = ChemistryEngine.canonicalize_smiles(Chem.MolToSmiles(mol, canonical=True))
    return mol, canonical, error


def search_structure(payload: dict[str, Any]) -> dict[str, Any]:
    molblock = str(payload.get("molblock") or "")
    input_format = "molblock" if molblock.strip() else "smiles"
    structure = molblock if input_format == "molblock" else str(payload.get("smiles") or payload.get("structure") or "").strip()
    role = str(payload.get("role") or "scaffold").strip().lower() or "scaffold"
    mode = str(payload.get("mode") or "similarity").strip().lower()
    threshold = safe_float(payload.get("threshold"), _DEFAULT_SIMILARITY_THRESHOLD)
    limit = safe_int(payload.get("limit"), 25)
    query_mol, canonical, error = parse_structure(structure)
    if error or query_mol is None or canonical is None:
        return {
            "matches": [],
            "metadata": metadata(0, "validation", empty_state_reason=error or "Invalid structure."),
            "validation_error": error or "Invalid structure.",
        }

    matches: list[dict[str, Any]] = []
    query_fp = AllChem.GetMorganFingerprintAsBitVect(query_mol, _MORGAN_RADIUS, nBits=_MORGAN_BITS)
    for scaffold in ScaffoldService.list_registered_scaffolds(limit=1000):
        target_smiles = str(scaffold.get("canonical_smiles") or "")
        target_mol = Chem.MolFromSmiles(target_smiles)
        if target_mol is None:
            continue
        similarity = DataStructs.TanimotoSimilarity(query_fp, AllChem.GetMorganFingerprintAsBitVect(target_mol, _MORGAN_RADIUS, nBits=_MORGAN_BITS))
        exact = Chem.MolToSmiles(target_mol, canonical=True) == canonical
        substructure = target_mol.HasSubstructMatch(query_mol) or query_mol.HasSubstructMatch(target_mol)
        include = exact if mode == "exact" else substructure if mode == "substructure" else similarity >= threshold or exact or substructure
        if not include:
            continue
        literature = search_literature(str(scaffold.get("name") or ""), limit=5)["items"]
        matches.append(
            {
                "match_id": f"scaffold:{scaffold.get('name', '')}",
                "name": scaffold.get("name", ""),
                "role": role,
                "canonical_smiles": target_smiles,
                "match_type": "exact" if exact else "substructure" if substructure else "similarity",
                "similarity": round(float(similarity), 3),
                "matched_publications": literature,
                "matched_records": literature,
                "matched_scaffold": scaffold.get("name", ""),
                "matched_reactions": [],
                "matched_structure_roles": [role, scaffold.get("category", ""), scaffold.get("family", "")],
            }
        )

    matches = sorted(matches, key=lambda item: (-float(item["similarity"]), str(item["name"])))[:limit]
    return {
        "matches": matches,
        "query": {"role": role, "mode": mode, "input_format": input_format, "canonical_smiles": canonical},
        "metadata": metadata(len(matches), "scaffold_entries/bronze_core_publications"),
    }