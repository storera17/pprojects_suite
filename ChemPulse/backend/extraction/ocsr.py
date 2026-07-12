from __future__ import annotations

from typing import Any

from backend.extraction.capabilities import ExtractionCapabilities, detect_capabilities


def recognize_schemes(
    scheme_images: list[dict[str, Any]], capabilities: ExtractionCapabilities | None = None
) -> dict[str, Any]:
    """Parse reactant/product SMILES from scheme images when an OCSR model is available."""
    capabilities = capabilities or detect_capabilities()
    if not scheme_images:
        return {"status": "no_images", "engine": None, "results": []}

    if capabilities.ocsr:
        return _run_openchemie(scheme_images)  # pragma: no cover - requires the model
    if capabilities.ocsr_fallback:
        return _run_decimer(scheme_images)  # pragma: no cover - requires the model

    return {
        "status": "skipped_no_ocsr",
        "engine": None,
        "results": [],
        "note": "No OCSR model installed (OpenChemIE/DECIMER); scheme images left pending.",
    }


def _run_openchemie(scheme_images: list[dict[str, Any]]) -> dict[str, Any]:  # pragma: no cover
    from openchemie import OpenChemIE  # type: ignore

    engine = OpenChemIE()
    results = []
    for image in scheme_images:
        path = image.get("image_path")
        if not path:
            continue
        parsed = engine.extract_reactions_from_figures([path])
        results.append({"image_id": image.get("image_id"), "reactions": parsed})
    return {"status": "ok", "engine": "openchemie", "results": results}


def _run_decimer(scheme_images: list[dict[str, Any]]) -> dict[str, Any]:  # pragma: no cover
    from DECIMER import predict_SMILES  # type: ignore

    results = []
    for image in scheme_images:
        path = image.get("image_path")
        if not path:
            continue
        results.append({"image_id": image.get("image_id"), "smiles": predict_SMILES(path)})
    return {"status": "ok", "engine": "decimer", "results": results}
