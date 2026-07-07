from __future__ import annotations

from typing import Any

from backend.data.core_publication_repository import ensure_core_ingestion_schema
from backend.data.db import query_records, table_exists
from backend.search.search_common import items_response, json_words, terms
from backend.services.scaffold_service import ScaffoldService

_TEXT_MATCH_SCORE = 18
_LINKED_SCAFFOLD_BONUS = 12
_REACTION_LABELS = (
    "esterification",
    "nucleophilic substitution",
    "amide coupling",
    "suzuki",
    "aldol",
    "oxidation",
    "reduction",
)


def search_literature(query: str = "", limit: int = 25) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        return items_response([], "bronze_core_publications/scaffold_entries", "Add a topic, scaffold, reaction, catalyst, or journal term.")

    publications = _publication_records(limit=max(limit * 4, limit))
    scaffolds = ScaffoldService.list_registered_scaffolds(limit=1000, query=cleaned_query)
    query_terms = terms(cleaned_query)
    items: list[dict[str, Any]] = []

    for publication in publications:
        haystack = _publication_text(publication)
        score = _score_text(haystack, query_terms)
        linked_scaffolds = _linked_scaffolds(haystack, scaffolds)
        if linked_scaffolds:
            score += _LINKED_SCAFFOLD_BONUS
        if score <= 0:
            continue
        matched_fields = _matched_fields(publication, query_terms)
        items.append(
            {
                "publication_id": publication["core_id"],
                "document_id": publication["core_id"],
                "title": publication["title"],
                "journal": publication["journal"] or "Unknown source",
                "source": publication["journal"] or "Unknown source",
                "year": publication["year_published"] or "",
                "date": publication["published_date"] or "",
                "matched_fields": matched_fields or ["abstract"],
                "highlighted_snippets": _snippets(publication, query_terms),
                "relevance_score": min(100, score),
                "linked_scaffolds": linked_scaffolds,
                "linked_reactions": _reaction_labels(haystack),
                "doi": publication["doi"] or "",
                "url": publication["source_url"] or publication["full_text_url"] or "",
            }
        )

    for scaffold in scaffolds:
        text = f"{scaffold.get('name', '')} {scaffold.get('category', '')} {scaffold.get('family', '')} {scaffold.get('canonical_smiles', '')}"
        score = _score_text(text, query_terms)
        if score <= 0:
            continue
        items.append(
            {
                "publication_id": "",
                "document_id": f"scaffold:{scaffold.get('name', '')}",
                "title": f"Scaffold record: {scaffold.get('name', '')}",
                "journal": scaffold.get("family") or "Scaffold registry",
                "source": "scaffold_entries",
                "year": "",
                "date": "",
                "matched_fields": ["name", "category", "family", "canonical_smiles"],
                "highlighted_snippets": [text],
                "relevance_score": min(100, score),
                "linked_scaffolds": [scaffold.get("name", "")],
                "linked_reactions": [],
                "doi": "",
                "url": "",
            }
        )

    items = sorted(items, key=lambda item: (-int(item["relevance_score"]), str(item["title"])))[:limit]
    return items_response(items, "bronze_core_publications/scaffold_entries")


def _publication_records(limit: int = 100) -> list[dict[str, Any]]:
    ensure_core_ingestion_schema()
    if not table_exists("bronze_core_publications"):
        return []
    rows = query_records(
        """
        SELECT core_id, title, doi, year_published, published_date, authors_json, journal,
               abstract, topics_json, full_text_url, source_url
        FROM bronze_core_publications
        ORDER BY fetched_at DESC, year_published DESC NULLS LAST, title ASC
        LIMIT ?
        """,
        [limit],
    )
    return [
        {
            **row,
            "title": row["title"] or "",
            "doi": row["doi"] or "",
            "authors_json": row["authors_json"] or "[]",
            "journal": row["journal"] or "Unknown source",
            "abstract": row["abstract"] or "",
            "topics_json": row["topics_json"] or "[]",
            "full_text_url": row["full_text_url"] or "",
            "source_url": row["source_url"] or "",
            "published_date": row["published_date"] or "",
        }
        for row in rows
    ]


def _publication_text(publication: dict[str, Any]) -> str:
    return " ".join(
        [
            str(publication.get("title", "")),
            str(publication.get("journal", "")),
            str(publication.get("doi", "")),
            json_words(publication.get("authors_json", "")),
            str(publication.get("abstract", "")),
            json_words(publication.get("topics_json", "")),
        ]
    )


def _score_text(text: str, query_terms: list[str]) -> int:
    lower = text.lower()
    return sum(_TEXT_MATCH_SCORE if term in lower else 0 for term in query_terms)


def _matched_fields(publication: dict[str, Any], query_terms: list[str]) -> list[str]:
    fields = {
        "title": publication.get("title", ""),
        "abstract": publication.get("abstract", ""),
        "journal": publication.get("journal", ""),
        "authors": json_words(publication.get("authors_json", "")),
        "keywords": json_words(publication.get("topics_json", "")),
        "doi": publication.get("doi", ""),
    }
    return [name for name, value in fields.items() if any(term in str(value).lower() for term in query_terms)]


def _snippets(publication: dict[str, Any], query_terms: list[str]) -> list[str]:
    fields = [publication.get("title", ""), publication.get("abstract", ""), json_words(publication.get("topics_json", ""))]
    snippets = []
    for field in fields:
        text = str(field or "")
        lower = text.lower()
        for term in query_terms:
            index = lower.find(term)
            if index >= 0:
                start = max(0, index - 80)
                end = min(len(text), index + 160)
                snippets.append(text[start:end].strip())
                break
    return snippets[:3] or [str(publication.get("title", ""))]


def _linked_scaffolds(text: str, scaffolds: list[dict[str, Any]]) -> list[str]:
    lower = text.lower()
    return [str(row.get("name")) for row in scaffolds if str(row.get("name") or "").lower() in lower][:8]


def _reaction_labels(text: str) -> list[str]:
    lower = text.lower()
    return [label for label in _REACTION_LABELS if label in lower]


