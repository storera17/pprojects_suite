from __future__ import annotations

from typing import Any

from backend.search.chemical_intelligence_service import ChemicalIntelligenceService, stable_report_id


class ReactionReportService:
    @staticmethod
    def generate(payload: dict[str, Any]) -> dict[str, Any]:
        reaction = ChemicalIntelligenceService.search_reaction(payload)
        explanation = ChemicalIntelligenceService.explain_mechanism(payload)
        citations = _citations(reaction.get("matched_publications", []))
        report_payload = {
            "query": payload,
            "reaction": reaction,
            "explanation": explanation,
            "citations": citations,
        }
        report_id = stable_report_id(report_payload)
        markdown = _markdown(report_id, payload, reaction, explanation, citations)
        return {
            "report_id": report_id,
            "markdown": markdown,
            "citations": citations,
            "confidence": explanation.get("confidence", 0.0),
            "metadata": {
                "record_count": len(citations),
                "source": "local_chemical_intelligence",
                "empty_state_reason": "" if citations else "No local literature citations were available for this report.",
            },
        }


def _citations(publications: list[dict[str, Any]]) -> list[dict[str, str]]:
    citations = []
    for item in publications[:12]:
        citations.append(
            {
                "publication_id": str(item.get("publication_id") or ""),
                "title": str(item.get("title") or "Untitled"),
                "journal": str(item.get("journal") or "Unknown source"),
                "year": str(item.get("year") or ""),
                "doi": str(item.get("doi") or ""),
            }
        )
    return citations


def _markdown(
    report_id: str,
    query: dict[str, Any],
    reaction: dict[str, Any],
    explanation: dict[str, Any],
    citations: list[dict[str, str]],
) -> str:
    candidates = reaction.get("candidate_reactions", [])
    lines = [
        "# ChemPulse Explained Reaction Report",
        "",
        f"- Report ID: `{report_id}`",
        f"- Confidence: `{explanation.get('confidence', 0.0)}`",
        "- Evidence basis: local ChemPulse literature/scaffold records plus conservative RDKit-assisted heuristics.",
        "",
        "## Reaction Query Summary",
        "",
        f"```json\n{_compact_json(query)}\n```",
        "",
        "## Candidate Mechanism Ranking",
        "",
    ]
    if candidates:
        for index, candidate in enumerate(candidates, start=1):
            lines.append(
                f"{index}. **{candidate.get('mechanism_name', 'Unknown')}** - confidence `{candidate.get('confidence', 0)}`; evidence score `{candidate.get('evidence_score', 0)}`."
            )
    else:
        lines.append("No candidate mechanisms were identified from local evidence.")

    lines.extend(["", "## Selected Mechanism Explanation", ""])
    for step in explanation.get("steps", []):
        lines.append(f"- **{step.get('title', 'Step')}**: {step.get('description', '')} _({step.get('basis', 'inference')})_")

    lines.extend(["", "## Evidence", ""])
    for evidence in explanation.get("evidence", []) or ["No evidence items were available."]:
        lines.append(f"- {evidence}")

    lines.extend(["", "## Main-Product and Competing-Product Rationale", ""])
    lines.append(
        "ChemPulse treats the proposed main product as an inference unless a matched local publication directly supports the same substrate/product/catalyst context. Competing products and by-products require explicit submitted structures or local evidence."
    )

    lines.extend(["", "## Limitations", ""])
    for warning in explanation.get("warnings", []):
        lines.append(f"- {warning}")
    for limitation in explanation.get("limitations", []):
        lines.append(f"- {limitation}")

    lines.extend(["", "## Citations", ""])
    if citations:
        for citation in citations:
            doi = f" DOI: `{citation['doi']}`" if citation.get("doi") else ""
            lines.append(f"- `{citation['publication_id']}` {citation['title']} ({citation['journal']}, {citation['year']}).{doi}")
    else:
        lines.append("No matched local literature citations were available.")
    return "\n".join(lines) + "\n"


def _compact_json(value: dict[str, Any]) -> str:
    import json

    return json.dumps(value, indent=2, sort_keys=True, default=str)
