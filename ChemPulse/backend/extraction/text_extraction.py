from __future__ import annotations

import re
from typing import Any

_YIELD_PATTERNS = [
    re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%\s*yield", re.IGNORECASE),
    re.compile(r"yield[:\s]*(?:of\s*)?(\d{1,3}(?:\.\d+)?)\s*%", re.IGNORECASE),
]
_TEMPERATURE_PATTERN = re.compile(r"(-?\d{1,3}(?:\.\d+)?)\s*(?:°|º)?\s*C\b")
_TIME_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?|min|days?|d)\b", re.IGNORECASE)
_ATMOSPHERE_PATTERNS = [
    (re.compile(r"\b(?:under\s+)?(?:nitrogen|N2)\b", re.IGNORECASE), "N2"),
    (re.compile(r"\b(?:under\s+)?(?:argon|Ar)\b(?!\w)", re.IGNORECASE), "Ar"),
    (re.compile(r"\bunder\s+(?:an?\s+)?inert\b", re.IGNORECASE), "inert"),
]
_SPECTRA_MARKERS = [
    (re.compile(r"1\s*H\s*NMR", re.IGNORECASE), "1H_NMR"),
    (re.compile(r"13\s*C\s*NMR", re.IGNORECASE), "13C_NMR"),
    (re.compile(r"\bHRMS\b", re.IGNORECASE), "HRMS"),
    (re.compile(r"\bLC[-\s]?MS\b", re.IGNORECASE), "LCMS"),
    (re.compile(r"\bGC[-\s]?MS\b", re.IGNORECASE), "GCMS"),
    (re.compile(r"\bIR\b", re.IGNORECASE), "IR"),
]
_PPM_PATTERN = re.compile(r"(\d+\.\d+)")


def extract_yield(text: str) -> float | None:
    for pattern in _YIELD_PATTERNS:
        match = pattern.search(text)
        if match:
            return float(match.group(1))
    return None


def extract_temperature_c(text: str) -> float | None:
    match = _TEMPERATURE_PATTERN.search(text)
    return float(match.group(1)) if match else None


def extract_time(text: str) -> str | None:
    match = _TIME_PATTERN.search(text)
    return f"{match.group(1)} {match.group(2)}" if match else None


def extract_atmosphere(text: str) -> str | None:
    for pattern, label in _ATMOSPHERE_PATTERNS:
        if pattern.search(text):
            return label
    return None


def extract_spectra(text: str) -> list[dict[str, Any]]:
    """Detect spectra blocks and capture the reported text + numeric peaks for each kind."""
    spectra: list[dict[str, Any]] = []
    for pattern, kind in _SPECTRA_MARKERS:
        match = pattern.search(text)
        if not match:
            continue
        window = text[match.start() : match.start() + 240]
        clause = re.split(r"(?<=\))\s*\.|\n", window, maxsplit=1)[0].strip()
        peaks = [float(p) for p in _PPM_PATTERN.findall(clause)] if kind in {"1H_NMR", "13C_NMR"} else []
        spectra.append({"kind": kind, "raw_text": clause, "peaks": peaks})
    return spectra


def extract_conditions(text: str) -> dict[str, Any]:
    """Regex-based structured conditions from a procedure paragraph (always runs)."""
    return {
        "yield_pct": extract_yield(text),
        "temperature_c": extract_temperature_c(text),
        "time_text": extract_time(text),
        "atmosphere": extract_atmosphere(text),
        "spectra": extract_spectra(text),
    }


def llm_enrich(procedure_text: str, *, base_url: str = "", model: str = "") -> dict[str, Any]:
    """Best-effort LLM pass for catalyst/solvent role disambiguation + mechanism narrative.

    Returns ``mechanism_source = "not_available"`` when the local LLM is unreachable, so the
    system never fabricates a mechanism. When reachable, the model is instructed to output
    "not stated" rather than invent an answer, and its output is tagged ``inferred_by_model``.
    """
    if not procedure_text.strip():
        return {"mechanism": [], "mechanism_source": "not_available", "mechanism_confidence": 0.0}
    try:
        from backend.ai.ollama_client import OllamaClient
        from backend.config import get_config

        config = get_config()
        client = OllamaClient(base_url=base_url or config.ollama_base_url, model=model or config.ollama_model)
        prompt = _mechanism_prompt(procedure_text)
        response = client.chat(prompt).strip()
    except Exception:
        return {"mechanism": [], "mechanism_source": "not_available", "mechanism_confidence": 0.0}

    if not response or "not stated" in response.lower():
        return {"mechanism": [], "mechanism_source": "not_available", "mechanism_confidence": 0.0}
    return {
        "mechanism": [{"description": response}],
        "mechanism_source": "inferred_by_model",
        "mechanism_confidence": 0.4,
    }


def _mechanism_prompt(procedure_text: str) -> str:
    return (
        "You are extracting reaction mechanism rationale from a procedure. If the authors do "
        "not state a mechanism, reply exactly 'not stated'. Do not invent one.\n\n"
        f"Procedure:\n{procedure_text[:1500]}\n\nMechanism (or 'not stated'):"
    )
