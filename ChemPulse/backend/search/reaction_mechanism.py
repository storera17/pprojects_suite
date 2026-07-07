from __future__ import annotations

import re
from typing import Any

from backend.search.literature_search import search_literature
from backend.search.reaction_families import REACTION_FAMILIES, fuzzy_alias_hits
from backend.search.search_common import items_response, metadata, safe_int, terms
from backend.search.structure_matching import parse_structure

_ROLE_NAMES = ("substrate", "product", "catalyst", "reagent", "byproduct", "intermediate", "scaffold")
_LOW_CONFIDENCE_THRESHOLD = 0.5


def search_reaction_name(payload: dict[str, Any]) -> dict[str, Any]:
    query = str(payload.get("query") or payload.get("reaction_name") or payload.get("name") or "").strip()
    limit = safe_int(payload.get("limit"), 20)
    if not query:
        return {
            "items": [],
            "aliases": [],
            "matched_publications": [],
            "metadata": metadata(0, "reaction_family_catalog", empty_state_reason="Enter a reaction or mechanism name."),
        }

    query_terms = terms(query)
    items = []
    all_aliases: list[str] = []
    publication_hits: dict[str, dict[str, Any]] = {}
    for family in REACTION_FAMILIES:
        family_text = " ".join(
            [family["name"], family["mechanism_class"], " ".join(family["aliases"]), " ".join(family["keywords"])]
        )
        exact_aliases = [alias for alias in family["aliases"] if alias.lower() == query.lower()]
        partial_aliases = [alias for alias in family["aliases"] if query.lower() in alias.lower() or alias.lower() in query.lower()]
        token_hits = [term for term in query_terms if term in family_text.lower()]
        fuzzy_hits = fuzzy_alias_hits(query, family["aliases"] + [family["name"]])
        if not exact_aliases and not partial_aliases and not token_hits and not fuzzy_hits:
            continue

        matched_aliases = list(dict.fromkeys(exact_aliases + partial_aliases + fuzzy_hits))
        all_aliases.extend(matched_aliases or family["aliases"][:2])
        publication_matches = search_literature(" ".join([family["name"], *family["aliases"], *family["keywords"]]), limit=5)["items"]
        for publication in publication_matches:
            publication_id = str(publication.get("publication_id") or publication.get("document_id") or "")
            if publication_id:
                publication_hits[publication_id] = publication
        score = min(
            1.0,
            0.35
            + 0.25 * len(exact_aliases)
            + 0.12 * len(partial_aliases)
            + 0.08 * len(token_hits)
            + 0.06 * len(fuzzy_hits)
            + 0.03 * len(publication_matches),
        )
        items.append(
            {
                "reaction_id": family["id"],
                "name": family["name"],
                "family": family["name"],
                "mechanism_class": family["mechanism_class"],
                "aliases": matched_aliases or family["aliases"],
                "matched_aliases": matched_aliases,
                "keywords": family["keywords"],
                "relevance_score": round(score, 3),
                "confidence": round(score, 3),
                "matched_publications": publication_matches,
            }
        )

    items = sorted(items, key=lambda item: (-float(item["relevance_score"]), str(item["name"])))[:limit]
    return {
        "items": items,
        "aliases": list(dict.fromkeys(all_aliases))[:25],
        "matched_publications": list(publication_hits.values()),
        "metadata": metadata(len(items), "reaction_family_catalog/bronze_core_publications", empty_state_reason="" if items else "No reaction family matched that name."),
    }


def search_reaction(payload: dict[str, Any]) -> dict[str, Any]:
    roles = _reaction_roles(payload)
    normalized_roles: dict[str, list[dict[str, str]]] = {}
    validation_errors: list[str] = []
    for role, values in roles.items():
        normalized_roles[role] = []
        for entry in values:
            value = entry["value"]
            _mol, canonical, error = parse_structure(value)
            if error:
                validation_errors.append(f"{role}: {error}")
                normalized_roles[role].append(
                    {"input": value, "input_format": entry["input_format"], "canonical_smiles": "", "validation_error": error}
                )
            else:
                normalized_roles[role].append(
                    {"input": value, "input_format": entry["input_format"], "canonical_smiles": canonical or "", "validation_error": ""}
                )

    text_query = _reaction_text_query(payload, normalized_roles)
    matched_publications = search_literature(text_query, limit=8)["items"] if text_query else []
    name_matches = search_reaction_name({"query": _reaction_name_query(payload), "limit": 8})
    candidates = _rank_mechanisms(payload, normalized_roles, matched_publications, name_matches.get("items", []))
    warnings = []
    if validation_errors:
        warnings.append("One or more drawn or pasted reaction structures could not be validated.")
    if candidates and float(candidates[0].get("confidence", 0)) < _LOW_CONFIDENCE_THRESHOLD:
        warnings.append("Low-confidence reaction match; use the evidence and missing-evidence notes before acting on this mechanism.")
    return {
        "candidate_reactions": candidates,
        "matched_publications": matched_publications,
        "validated_inputs": normalized_roles,
        "query": {"roles": normalized_roles, "text_query": text_query, "reaction_name": _reaction_name_query(payload)},
        "metadata": metadata(len(candidates), "bronze_core_publications/scaffold_entries", empty_state_reason="" if candidates else "No local reaction evidence matched this query."),
        "validation_errors": validation_errors,
        "warnings": warnings,
    }


def explain_mechanism(payload: dict[str, Any]) -> dict[str, Any]:
    reaction = search_reaction(payload)
    selected = (reaction.get("candidate_reactions") or [_fallback_candidate(payload)])[0]
    confidence = float(selected.get("confidence", 0.18))
    warnings = list(selected.get("warnings") or [])
    if confidence < _LOW_CONFIDENCE_THRESHOLD:
        warnings.append("Low-confidence mechanistic inference: ChemPulse did not find enough local literature evidence for a definitive mechanism.")
    steps = _arrow_steps(selected.get("mechanism_name", ""), payload)
    return {
        "steps": steps,
        "evidence": selected.get("evidence", []),
        "confidence": round(confidence, 3),
        "warnings": list(dict.fromkeys(warnings)),
        "limitations": selected.get("missing_evidence", []),
        "selected_mechanism": selected.get("mechanism_name", "General polar organic transformation"),
        "matched_publications": reaction.get("matched_publications", []),
        "metadata": metadata(len(steps), "local_heuristics/bronze_core_publications"),
    }


def _reaction_roles(payload: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    roles: dict[str, list[dict[str, str]]] = {}
    for role in _ROLE_NAMES:
        raw = payload.get(role) or payload.get(f"{role}s") or []
        if isinstance(raw, str):
            values = [{"value": part.strip(), "input_format": _structure_input_format(part)} for part in re.split(r"[;,\n]+", raw) if part.strip()]
        elif isinstance(raw, list):
            values = [_reaction_role_entry(part) for part in raw]
            values = [entry for entry in values if entry["value"].strip()]
        elif isinstance(raw, dict):
            entry = _reaction_role_entry(raw)
            values = [entry] if entry["value"].strip() else []
        else:
            values = []
        roles[role] = values
    return roles


def _reaction_text_query(payload: dict[str, Any], normalized_roles: dict[str, list[dict[str, str]]]) -> str:
    bits = [_reaction_name_query(payload)]
    for records in normalized_roles.values():
        for record in records:
            bits.append(record.get("input", ""))
            bits.append(record.get("canonical_smiles", ""))
    return " ".join(bit for bit in bits if bit).strip()


def _reaction_role_entry(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        raw = str(value.get("molblock") or value.get("smiles") or value.get("structure") or value.get("value") or "")
        fmt = str(value.get("input_format") or ("molblock" if value.get("molblock") else "smiles"))
        return {"value": raw, "input_format": fmt}
    raw = str(value or "").strip()
    return {"value": raw, "input_format": _structure_input_format(raw)}


def _structure_input_format(value: str) -> str:
    return "molblock" if "\n" in str(value or "") and "M  END" in str(value or "") else "smiles"


def _reaction_name_query(payload: dict[str, Any]) -> str:
    return str(payload.get("reaction_name") or payload.get("name") or payload.get("query") or payload.get("mechanism_hint") or "").strip()


def _rank_mechanisms(
    payload: dict[str, Any],
    roles: dict[str, list[dict[str, str]]],
    publications: list[dict[str, Any]],
    name_matches: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    text = f"{payload} {' '.join(pub.get('title', '') + ' ' + ' '.join(pub.get('highlighted_snippets', [])) for pub in publications)}".lower()
    name_matches_by_id = {str(item.get("reaction_id")): item for item in (name_matches or [])}
    candidates = []
    for family in REACTION_FAMILIES:
        name = family["name"]
        keywords = family["keywords"]
        name_match = name_matches_by_id.get(family["id"])
        keyword_hits = [keyword for keyword in keywords if keyword in text]
        role_score = 0.08 * sum(1 for role in ("substrate", "product", "catalyst", "reagent") if roles.get(role))
        publication_score = min(0.35, 0.07 * len(publications))
        name_score = float(name_match.get("confidence", 0)) * 0.34 if name_match else 0.0
        confidence = min(0.94, 0.16 + name_score + role_score + publication_score + 0.07 * len(keyword_hits))
        if name_match or keyword_hits or publications or role_score:
            candidates.append(
                {
                    "mechanism_name": name,
                    "reaction_family": name,
                    "likely_mechanism_class": family["mechanism_class"],
                    "matched_aliases": list(name_match.get("matched_aliases") or name_match.get("aliases") or []) if name_match else [],
                    "confidence": round(confidence, 3),
                    "evidence_score": round(confidence * 100, 1),
                    "evidence": _evidence_items(keyword_hits, publications, roles),
                    "matched_publication_ids": [pub.get("publication_id") for pub in publications[:5] if pub.get("publication_id")],
                    "matched_publications": publications[:5],
                    "matched_substrates": _canonical_role_values(roles, "substrate"),
                    "matched_products": _canonical_role_values(roles, "product"),
                    "matched_catalysts": _canonical_role_values(roles, "catalyst") + _canonical_role_values(roles, "reagent"),
                    "matched_byproducts": _canonical_role_values(roles, "byproduct"),
                    "missing_evidence": _missing_evidence(roles, publications, keyword_hits),
                    "warnings": [] if confidence >= _LOW_CONFIDENCE_THRESHOLD else ["Evidence is limited; treat this mechanism as a hypothesis."],
                }
            )
    if not candidates:
        candidates.append(_fallback_candidate(payload))
    return sorted(candidates, key=lambda item: -float(item["confidence"]))[:5]


def _canonical_role_values(roles: dict[str, list[dict[str, str]]], role: str) -> list[str]:
    return [record.get("canonical_smiles") or record.get("input", "") for record in roles.get(role, []) if not record.get("validation_error")]


def _fallback_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mechanism_name": str(payload.get("mechanism_hint") or "General polar organic transformation"),
        "confidence": 0.18,
        "evidence_score": 18.0,
        "evidence": ["No strong local literature or role evidence found."],
        "matched_publication_ids": [],
        "missing_evidence": ["No exact local literature match.", "No mapped atom correspondence.", "No experimentally confirmed by-product profile."],
        "warnings": ["Low-confidence heuristic result."],
    }


def _arrow_steps(mechanism_name: str, payload: dict[str, Any]) -> list[dict[str, str]]:
    name = mechanism_name.lower()
    if "ester" in name or "acyl" in name:
        return [
            _step("Nucleophile/electrophile", "A heteroatom nucleophile attacks an activated carbonyl electrophile.", "inference"),
            _step("Bond formed", "A new C-O or C-N sigma bond forms at the acyl carbon.", "inference"),
            _step("Bond broken", "The acyl leaving group departs as the tetrahedral intermediate collapses.", "inference"),
            _step("Proton transfer", "Proton transfers regenerate a neutral product and catalyst/base when present.", "inference"),
            _step("Main product rationale", "The product is favored when the submitted product preserves the acyl substitution pattern and removes the best leaving group.", "inference"),
        ]
    if "substitution" in name:
        return [
            _step("Nucleophile/electrophile", "The nucleophile approaches the electrophilic carbon bearing a leaving group.", "inference"),
            _step("Bond formed", "A new sigma bond forms between the nucleophile and electrophilic carbon.", "inference"),
            _step("Bond broken", "The C-leaving-group bond breaks either concertedly or through an ion-pair-like intermediate.", "inference"),
            _step("Selectivity", "Primary unhindered centers favor direct displacement; stabilized centers may favor stepwise substitution.", "inference"),
        ]
    if "suzuki" in name:
        return [
            _step("Oxidative addition", "Pd inserts into an aryl-halide or related electrophile bond.", "inference"),
            _step("Transmetalation", "The organoboron partner transfers the organic group to palladium under base assistance.", "inference"),
            _step("Reductive elimination", "The C-C bond forms as Pd returns to a lower oxidation state.", "inference"),
            _step("Main product rationale", "The cross-coupled product follows from pairing the submitted aryl/alkenyl fragments.", "inference"),
        ]
    return [
        _step("Evidence triage", "ChemPulse found limited local evidence, so this is a conservative mechanistic scaffold.", "limitation"),
        _step("Reactive partners", "Identify the most electron-rich submitted species as nucleophile and the most electron-poor species as electrophile.", "inference"),
        _step("Bond changes", "Compare submitted substrates and products to locate likely bonds formed and broken.", "inference"),
        _step("Limitations", "Atom mapping, transition states, solvent effects, and competing pathways are not proven by this local heuristic.", "limitation"),
    ]


def _step(title: str, description: str, basis: str) -> dict[str, str]:
    return {"title": title, "description": description, "basis": basis}


def _evidence_items(keyword_hits: list[str], publications: list[dict[str, Any]], roles: dict[str, list[dict[str, str]]]) -> list[str]:
    evidence = [f"Keyword evidence: {', '.join(keyword_hits)}"] if keyword_hits else []
    if publications:
        evidence.append(f"{len(publications)} local publication match(es) contributed evidence.")
    for role, records in roles.items():
        if records:
            evidence.append(f"{role} role supplied: {', '.join(record.get('canonical_smiles') or record.get('input', '') for record in records)}")
    return evidence or ["Heuristic mechanism family selected from submitted roles."]


def _missing_evidence(roles: dict[str, list[dict[str, str]]], publications: list[dict[str, Any]], keyword_hits: list[str]) -> list[str]:
    missing = []
    if not publications:
        missing.append("No matched local publication records.")
    if not keyword_hits:
        missing.append("No mechanism-family keyword evidence in matched local text.")
    if not roles.get("product"):
        missing.append("No product structure was supplied.")
    if not roles.get("substrate"):
        missing.append("No substrate structure was supplied.")
    missing.append("No atom-mapped reaction pathway dependency is installed.")
    return missing
