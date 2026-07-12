from __future__ import annotations

import hashlib
from typing import Any

from backend.data.reaction_repository import ReactionRepository

# source_kind -> default credibility tier (design §3.1).
SOURCE_TIER: dict[str, int] = {
    "core_api": 1,
    "open_reaction_database": 1,
    "uspto": 1,
    "supporting_info": 1,
    "textbook": 1,
    "pdf_local": 2,
    "preprint": 2,
    "manual_entry": 3,
}


def tier_for_source(source_kind: str) -> int:
    return SOURCE_TIER.get(source_kind, 3)


def acquire_documents(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Register documents into ``bronze_documents`` and return their stored shape.

    ``records`` items carry at least ``source_kind``; ``doc_id`` is derived from the DOI or
    URL when not supplied so re-ingesting the same paper updates one row (supporting later
    corroboration matching by DOI).
    """
    stored: list[dict[str, Any]] = []
    for record in records:
        source_kind = str(record.get("source_kind") or "manual_entry")
        doc_id = str(record.get("doc_id") or _derive_doc_id(record))
        tier = int(record.get("credibility_tier") or tier_for_source(source_kind))
        ReactionRepository.upsert_document(
            doc_id,
            source_kind,
            title=str(record.get("title") or ""),
            doi=str(record.get("doi") or ""),
            url=str(record.get("url") or ""),
            local_path=str(record.get("local_path") or ""),
            credibility_tier=tier,
            raw_text=record.get("raw_text"),
            meta=record.get("meta") or {},
        )
        stored.append({"doc_id": doc_id, "source_kind": source_kind, "credibility_tier": tier})
    return stored


def _derive_doc_id(record: dict[str, Any]) -> str:
    seed = str(record.get("doi") or record.get("url") or record.get("title") or record.get("raw_text") or "")
    if not seed:
        seed = repr(sorted(record.items()))
    return "doc_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:14]
