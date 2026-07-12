from __future__ import annotations

from typing import Any

from backend.data.reaction_repository import ReactionRepository
from backend.extraction import EXTRACTOR_VERSION


def normalize_and_write(reaction_record: dict[str, Any]) -> dict[str, Any]:
    """Write one extracted reaction into the silver layer, returning the stored row.

    Any spectra attached to the record are written to ``silver_spectra`` and linked to the
    (deduplicated) reaction id. If this exact reaction already exists from another source, the
    incoming yield is retained alongside the existing one under ``conflicting_values`` so no
    reported number is lost.
    """
    existing = None
    reactants = list(reaction_record.get("reactants") or [])
    products = list(reaction_record.get("products") or [])
    if reactants and products:
        signature = ReactionRepository.reaction_signature(reactants, products)
        existing = ReactionRepository.get_reaction(signature)

    record = dict(reaction_record)
    record.setdefault("extractor_version", EXTRACTOR_VERSION)

    incoming_yield = record.get("yield_pct")
    if existing and incoming_yield is not None and existing.get("yield_pct") not in (None, incoming_yield):
        stereo = dict(record.get("stereochemistry") or existing.get("stereochemistry") or {})
        conflicts = list(stereo.get("conflicting_values", []))
        conflicts.append(
            {
                "field": "yield_pct",
                "existing": existing.get("yield_pct"),
                "incoming": incoming_yield,
                "sources": record.get("source_doc_ids") or [],
            }
        )
        stereo["conflicting_values"] = conflicts
        record["stereochemistry"] = stereo

    stored = ReactionRepository.upsert_reaction(record)

    for spectrum in record.get("spectra") or []:
        ReactionRepository.add_spectrum(
            stored["reaction_id"],
            str(spectrum.get("kind") or "UNKNOWN"),
            peaks=spectrum.get("peaks") or [],
            raw_text=str(spectrum.get("raw_text") or ""),
            molecular_weight=spectrum.get("molecular_weight"),
            molecular_formula=str(spectrum.get("molecular_formula") or ""),
        )
    return stored
