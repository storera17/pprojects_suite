from __future__ import annotations

from typing import Any

from backend.extraction import EXTRACTOR_VERSION
from backend.extraction.atom_mapping import map_reaction
from backend.extraction.capabilities import detect_capabilities
from backend.extraction.normalize import normalize_and_write
from backend.extraction.ocsr import recognize_schemes
from backend.extraction.segment import segment_document
from backend.extraction.sources import acquire_documents
from backend.extraction.text_extraction import extract_conditions, llm_enrich


class ExtractionPipeline:
    @staticmethod
    def run(documents: list[dict[str, Any]], *, enable_llm: bool = False) -> dict[str, Any]:
        """Extract reactions from ``documents`` and persist them. Returns a per-stage report."""
        capabilities = detect_capabilities()
        report: dict[str, Any] = {
            "extractor_version": EXTRACTOR_VERSION,
            "capabilities": capabilities.as_dict(),
            "documents_processed": 0,
            "paragraphs": 0,
            "ocsr": {"parsed": 0, "skipped": 0},
            "atom_mapping": {"mapped": 0, "skipped": 0},
            "reactions_written": 0,
            "reactions_corroborated": 0,
            "skipped_stages": [],
            "errors": [],
        }

        # Stage 1 — Acquire.
        stored_docs = acquire_documents(documents)
        doc_id_by_index = {i: stored["doc_id"] for i, stored in enumerate(stored_docs)}
        report["documents_processed"] = len(stored_docs)

        if not capabilities.ocsr and not capabilities.ocsr_fallback:
            report["skipped_stages"].append("ocsr")
        if not capabilities.atom_mapper:
            report["skipped_stages"].append("atom_mapping")
        if not enable_llm:
            report["skipped_stages"].append("llm_enrich")

        for index, document in enumerate(documents):
            doc_id = doc_id_by_index.get(index)
            try:
                ExtractionPipeline._process_document(document, doc_id, capabilities, enable_llm, report)
            except Exception as exc:  # pragma: no cover - defensive; one bad doc shouldn't abort the batch
                report["errors"].append({"doc_index": index, "error": exc.__class__.__name__})

        return report

    @staticmethod
    def _process_document(
        document: dict[str, Any],
        doc_id: str | None,
        capabilities: Any,
        enable_llm: bool,
        report: dict[str, Any],
    ) -> None:
        # Stage 2 — Segment.
        segmented = segment_document(document, capabilities)
        report["paragraphs"] += len(segmented.get("paragraphs", []))

        # Stage 3 — OCSR (guarded).
        ocsr_result = recognize_schemes(segmented.get("figures", []), capabilities)
        if ocsr_result["status"].startswith("skipped"):
            report["ocsr"]["skipped"] += len(segmented.get("figures", []))
        else:
            report["ocsr"]["parsed"] += len(ocsr_result.get("results", []))

        reactions = list(document.get("reactions") or [])
        fallback_text = str(document.get("raw_text") or "")
        for reaction in reactions:
            enriched = ExtractionPipeline._enrich_reaction(
                reaction, doc_id, fallback_text, capabilities, enable_llm, report
            )
            stored = normalize_and_write(enriched)
            report["reactions_written"] += 1
            if int(stored.get("corroboration_count", 1)) > 1:
                report["reactions_corroborated"] += 1

    @staticmethod
    def _enrich_reaction(
        reaction: dict[str, Any],
        doc_id: str | None,
        fallback_text: str,
        capabilities: Any,
        enable_llm: bool,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        enriched = dict(reaction)
        if doc_id:
            source_ids = list(enriched.get("source_doc_ids") or [])
            if doc_id not in source_ids:
                source_ids.append(doc_id)
            enriched["source_doc_ids"] = source_ids

        # Stage 4 — Text extraction (regex conditions never overwrite explicit values).
        procedure = str(enriched.get("procedure_text") or fallback_text)
        conditions = extract_conditions(procedure)
        for key in ("yield_pct", "temperature_c", "time_text", "atmosphere"):
            if enriched.get(key) in (None, "") and conditions.get(key) is not None:
                enriched[key] = conditions[key]
        if not enriched.get("spectra") and conditions.get("spectra"):
            enriched["spectra"] = conditions["spectra"]

        if enable_llm:
            mechanism = llm_enrich(procedure)
            enriched.setdefault("mechanism", mechanism["mechanism"])
            enriched.setdefault("mechanism_source", mechanism["mechanism_source"])
            enriched.setdefault("mechanism_confidence", mechanism["mechanism_confidence"])

        # Stage 5 — Atom mapping (guarded).
        reaction_smiles = enriched.get("reaction_smiles") or _reaction_smiles(enriched)
        if reaction_smiles:
            mapping = map_reaction(reaction_smiles, capabilities)
            enriched["reaction_smiles"] = mapping["mapped_smiles"]
            enriched["reacting_atoms"] = mapping.get("reacting_atoms", [])
            if mapping["status"] == "ok":
                report["atom_mapping"]["mapped"] += 1
            else:
                report["atom_mapping"]["skipped"] += 1

        enriched.setdefault("extractor_version", EXTRACTOR_VERSION)
        return enriched


def _reaction_smiles(reaction: dict[str, Any]) -> str:
    reactants = ".".join(reaction.get("reactants") or [])
    products = ".".join(reaction.get("products") or [])
    return f"{reactants}>>{products}" if reactants and products else ""
