from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.data.reaction_repository import ReactionRepository
from backend.utils.paths import storage_dir
from backend.utils.xlsx import Sheet, write_workbook

_REACTION_COLUMNS: list[tuple[str, str]] = [
    ("reaction_id", "Reaction ID"),
    ("route_id", "Route ID"),
    ("step_index", "Step"),
    ("reaction_smiles", "Reaction SMILES"),
    ("reactants", "Reactants"),
    ("reagents", "Reagents"),
    ("catalysts", "Catalysts"),
    ("solvents", "Solvents"),
    ("products", "Products"),
    ("byproducts", "By-products"),
    ("temperature_c", "Temp (C)"),
    ("time_text", "Time"),
    ("atmosphere", "Atmosphere"),
    ("pressure_text", "Pressure"),
    ("yield_pct", "Yield (%)"),
    ("mechanism_source", "Mechanism Source"),
    ("mechanism_confidence", "Mechanism Confidence"),
    ("product_inchikey", "Product InChIKey"),
    ("corroboration_count", "Corroboration"),
    ("credibility_score", "Credibility"),
    ("source_doc_ids", "Source Documents"),
    ("extractor_version", "Extractor"),
    ("extracted_at", "Extracted At"),
    ("procedure_text", "Procedure"),
]

_SPECTRA_COLUMNS: list[tuple[str, str]] = [
    ("reaction_id", "Reaction ID"),
    ("kind", "Kind"),
    ("molecular_formula", "Formula"),
    ("molecular_weight", "MW"),
    ("peaks", "Peaks"),
    ("raw_text", "Reported Text"),
]

_DOCUMENT_COLUMNS: list[tuple[str, str]] = [
    ("doc_id", "Document ID"),
    ("source_kind", "Source Kind"),
    ("title", "Title"),
    ("doi", "DOI"),
    ("credibility_tier", "Tier"),
    ("url", "URL"),
    ("fetched_at", "Fetched At"),
]


class ReactionExportService:
    @staticmethod
    def export(path: str | Path | None = None, *, limit: int = 100_000) -> dict[str, Any]:
        """Write the current reaction dataset to ``path`` (or a timestamped default).

        Returns a small manifest describing what was written so callers/tests can assert
        counts without re-parsing the workbook.
        """
        reactions = ReactionRepository.list_reactions(limit=limit)
        documents = ReactionRepository.list_documents(limit=limit)

        reaction_rows: list[list[Any]] = []
        spectra_rows: list[list[Any]] = []
        for reaction in reactions:
            reaction_rows.append([_format(reaction.get(key)) for key, _ in _REACTION_COLUMNS])
            for spectrum in reaction.get("spectra") or ReactionRepository.spectra_for_reaction(reaction["reaction_id"]):
                spectra_rows.append([_format(spectrum.get(key)) for key, _ in _SPECTRA_COLUMNS])

        document_rows = [[_format(doc.get(key)) for key, _ in _DOCUMENT_COLUMNS] for doc in documents]

        sheets = [
            Sheet("Reactions", [label for _, label in _REACTION_COLUMNS], reaction_rows),
            Sheet("Spectra", [label for _, label in _SPECTRA_COLUMNS], spectra_rows),
            Sheet("Documents", [label for _, label in _DOCUMENT_COLUMNS], document_rows),
        ]

        target = Path(path) if path else _default_export_path()
        written = write_workbook(target, sheets)
        return {
            "ok": True,
            "path": str(written),
            "reaction_count": len(reaction_rows),
            "spectra_count": len(spectra_rows),
            "document_count": len(document_rows),
        }


def _default_export_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return storage_dir() / "exports" / f"chempulse-reactions-{stamp}.xlsx"


def _format(value: Any) -> Any:
    """Flatten roles/provenance lists and mechanism structures into spreadsheet-friendly cells."""
    if value is None:
        return ""
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, list):
        parts = [part if isinstance(part, str) else json.dumps(part, ensure_ascii=False) for part in value]
        return " | ".join(parts)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
