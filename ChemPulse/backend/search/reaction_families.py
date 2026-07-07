from __future__ import annotations

from typing import Any

from backend.search.search_common import terms

REACTION_FAMILIES: list[dict[str, Any]] = [
    {
        "id": "friedel-crafts-acylation",
        "name": "Friedel-Crafts acylation",
        "mechanism_class": "electrophilic aromatic substitution",
        "aliases": ["Friedel-Crafts acylation", "FC acylation", "aromatic acylation"],
        "keywords": ["friedel", "crafts", "acylation", "aryl ketone", "lewis acid", "acyl chloride", "anhydride"],
    },
    {
        "id": "friedel-crafts-alkylation",
        "name": "Friedel-Crafts alkylation",
        "mechanism_class": "electrophilic aromatic substitution",
        "aliases": ["Friedel-Crafts alkylation", "FC alkylation", "aromatic alkylation"],
        "keywords": ["friedel", "crafts", "alkylation", "carbocation", "lewis acid", "aryl alkane"],
    },
    {
        "id": "suzuki-coupling",
        "name": "Suzuki cross-coupling",
        "mechanism_class": "palladium-catalyzed cross-coupling",
        "aliases": ["Suzuki coupling", "Suzuki-Miyaura coupling", "Suzuki cross-coupling"],
        "keywords": ["suzuki", "miyaura", "boronic", "palladium", "aryl halide", "transmetalation"],
    },
    {
        "id": "heck-reaction",
        "name": "Heck reaction",
        "mechanism_class": "palladium-catalyzed alkene arylation",
        "aliases": ["Heck reaction", "Mizoroki-Heck reaction"],
        "keywords": ["heck", "mizoroki", "palladium", "alkene", "beta hydride"],
    },
    {
        "id": "sonogashira-coupling",
        "name": "Sonogashira coupling",
        "mechanism_class": "palladium/copper-catalyzed alkyne coupling",
        "aliases": ["Sonogashira coupling", "Sonogashira-Hagihara coupling"],
        "keywords": ["sonogashira", "alkyne", "copper", "palladium", "aryl halide"],
    },
    {
        "id": "diels-alder",
        "name": "Diels-Alder cycloaddition",
        "mechanism_class": "pericyclic cycloaddition",
        "aliases": ["Diels-Alder", "Diels Alder reaction", "4+2 cycloaddition"],
        "keywords": ["diels", "alder", "cycloaddition", "diene", "dienophile", "pericyclic"],
    },
    {
        "id": "aldol-condensation",
        "name": "Aldol condensation",
        "mechanism_class": "carbonyl addition-dehydration",
        "aliases": ["aldol condensation", "aldol addition", "enolate aldol"],
        "keywords": ["aldol", "enolate", "carbonyl", "aldehyde", "ketone", "dehydration"],
    },
    {
        "id": "grignard-addition",
        "name": "Grignard addition",
        "mechanism_class": "organomagnesium carbonyl addition",
        "aliases": ["Grignard addition", "Grignard reaction", "organomagnesium addition"],
        "keywords": ["grignard", "organomagnesium", "carbonyl", "alcohol", "nucleophilic addition"],
    },
    {
        "id": "wittig-reaction",
        "name": "Wittig reaction",
        "mechanism_class": "phosphonium ylide olefination",
        "aliases": ["Wittig reaction", "Wittig olefination"],
        "keywords": ["wittig", "ylide", "phosphonium", "olefin", "alkene"],
    },
    {
        "id": "sn1",
        "name": "SN1 substitution",
        "mechanism_class": "unimolecular nucleophilic substitution",
        "aliases": ["SN1", "S N 1", "unimolecular substitution"],
        "keywords": ["sn1", "substitution", "carbocation", "leaving group", "solvolysis"],
    },
    {
        "id": "sn2",
        "name": "SN2 substitution",
        "mechanism_class": "bimolecular nucleophilic substitution",
        "aliases": ["SN2", "S N 2", "bimolecular substitution"],
        "keywords": ["sn2", "substitution", "backside attack", "leaving group", "halide"],
    },
    {
        "id": "e1",
        "name": "E1 elimination",
        "mechanism_class": "unimolecular beta elimination",
        "aliases": ["E1", "unimolecular elimination"],
        "keywords": ["e1", "elimination", "carbocation", "alkene", "leaving group"],
    },
    {
        "id": "e2",
        "name": "E2 elimination",
        "mechanism_class": "concerted beta elimination",
        "aliases": ["E2", "bimolecular elimination"],
        "keywords": ["e2", "elimination", "anti periplanar", "base", "alkene"],
    },
    {
        "id": "esterification",
        "name": "Esterification or acyl transfer",
        "mechanism_class": "nucleophilic acyl substitution",
        "aliases": ["esterification", "Fischer esterification", "acyl transfer"],
        "keywords": ["ester", "esterification", "acyl", "carboxy", "anhydride", "acid chloride"],
    },
    {
        "id": "hydroboration-oxidation",
        "name": "Hydroboration oxidation",
        "mechanism_class": "alkene hydroboration and oxidative workup",
        "aliases": ["hydroboration oxidation", "hydroboration-oxidation"],
        "keywords": ["hydroboration", "borane", "oxidation", "anti markovnikov", "alkene"],
    },
    {
        "id": "epoxidation",
        "name": "Epoxidation",
        "mechanism_class": "alkene oxygen transfer",
        "aliases": ["epoxidation", "Prilezhaev reaction"],
        "keywords": ["epoxidation", "peracid", "mcpba", "alkene", "epoxide"],
    },
    {
        "id": "reductive-amination",
        "name": "Reductive amination",
        "mechanism_class": "imine formation and reduction",
        "aliases": ["reductive amination", "reductive alkylation"],
        "keywords": ["reductive amination", "imine", "iminium", "amine", "cyanoborohydride"],
    },
    {
        "id": "amide-coupling",
        "name": "Amide coupling",
        "mechanism_class": "activated carboxylate aminolysis",
        "aliases": ["amide coupling", "peptide coupling", "carboxamide formation"],
        "keywords": ["amide", "coupling", "edc", "hatu", "peptide", "carboxylate"],
    },
]


def fuzzy_alias_hits(query: str, choices: list[str]) -> list[str]:
    query_terms = set(terms(query))
    hits = []
    for choice in choices:
        choice_terms = set(terms(choice))
        if query_terms and choice_terms and len(query_terms & choice_terms) / max(len(query_terms | choice_terms), 1) >= 0.5:
            hits.append(choice)
    return hits
