from __future__ import annotations

import re
from typing import Any

from backend.extraction.capabilities import ExtractionCapabilities, detect_capabilities

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n|\r\n\s*\r\n")


def segment_text(raw_text: str) -> dict[str, Any]:
    """Split plain text into non-trivial paragraphs. No dependencies."""
    if not raw_text:
        return {"paragraphs": [], "figures": []}
    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(raw_text) if len(p.strip()) >= 20]
    if not paragraphs and raw_text.strip():
        paragraphs = [raw_text.strip()]
    return {"paragraphs": paragraphs, "figures": []}


def segment_document(document: dict[str, Any], capabilities: ExtractionCapabilities | None = None) -> dict[str, Any]:
    """Segment a stored document into paragraphs and figures.

    Uses PyMuPDF for a local PDF path when available; otherwise falls back to the document's
    already-extracted ``raw_text``.
    """
    capabilities = capabilities or detect_capabilities()
    local_path = str(document.get("local_path") or "")
    if capabilities.pymupdf and local_path.lower().endswith(".pdf"):
        try:
            return _segment_pdf(local_path)
        except Exception:  # pragma: no cover - depends on optional model + real file
            pass
    result = segment_text(str(document.get("raw_text") or ""))
    result["segmenter"] = "pymupdf" if capabilities.pymupdf else "text_fallback"
    return result


def _segment_pdf(path: str) -> dict[str, Any]:  # pragma: no cover - requires PyMuPDF + a real PDF
    import fitz  # type: ignore

    text_parts: list[str] = []
    figures: list[dict[str, Any]] = []
    with fitz.open(path) as pdf:
        for page_index, page in enumerate(pdf):
            text_parts.append(page.get_text("text"))
            for image_index, image in enumerate(page.get_images(full=True)):
                figures.append({"page": page_index, "xref": image[0], "index": image_index})
    result = segment_text("\n\n".join(text_parts))
    result["figures"] = figures
    result["segmenter"] = "pymupdf"
    return result
