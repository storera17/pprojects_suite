from __future__ import annotations

import importlib.util
from dataclasses import dataclass


def _available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


@dataclass(frozen=True)
class ExtractionCapabilities:
    pymupdf: bool
    ocsr: bool  # OpenChemIE (MolScribe/RxnScribe)
    ocsr_fallback: bool  # DECIMER
    chem_ner: bool  # ChemDataExtractor
    atom_mapper: bool  # RXNMapper
    llm: bool  # local Ollama reachable is checked separately; this is the client import

    def as_dict(self) -> dict[str, bool]:
        return {
            "pymupdf": self.pymupdf,
            "ocsr": self.ocsr,
            "ocsr_fallback": self.ocsr_fallback,
            "chem_ner": self.chem_ner,
            "atom_mapper": self.atom_mapper,
            "llm": self.llm,
        }


def detect_capabilities() -> ExtractionCapabilities:
    return ExtractionCapabilities(
        pymupdf=_available("fitz") or _available("pymupdf"),
        ocsr=_available("openchemie"),
        ocsr_fallback=_available("decimer"),
        chem_ner=_available("chemdataextractor") or _available("chemdataextractor2"),
        atom_mapper=_available("rxnmapper"),
        llm=_available("requests"),  # Ollama client uses requests; reachability checked at call time
    )
