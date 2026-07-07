from __future__ import annotations

HIGH_RELEVANCE_THRESHOLD = 70
MEDIUM_RELEVANCE_THRESHOLD = 40
LOW_RELEVANCE_THRESHOLD = 18
DEFAULT_MIN_INGESTION_RELEVANCE_SCORE = MEDIUM_RELEVANCE_THRESHOLD

# Change as needed 
FOCUS_TERMS: tuple[str, ...] = (
    "catalyst",
    "catalysis",
    "catalytic",
    "photocatalyst",
    "photocatalysis",
    "electrocatalyst",
    "electrocatalysis",
    "organocatalyst",
    "organocatalysis",
    "scaffold",
    "molecular scaffold",
    "chemical scaffold",
    "ligand",
    "cross-coupling",
    "suzuki",
    "buchwald",
    "sonogashira",
    "heck reaction",
    "heterocycle",
    "heterocyclic",
    "medicinal chemistry",
    "reaction mechanism",
    "esterification",
)

CHEMISTRY_CONTEXT_TERMS: tuple[str, ...] = (
    "chemistry",
    "chemical",
    "synthesis",
    "synthetic",
    "reaction",
    "molecule",
    "molecular",
    "compound",
    "organic",
    "inorganic",
    "materials",
    "nanoparticle",
    "polymer",
    "pharmaceutical",
)

SUPPORTING_SCAFFOLD_TERMS: tuple[str, ...] = (
    "pyridine",
    "indole",
    "quinoline",
    "benzoxazole",
    "taxane",
    "paclitaxel",
    "polyether",
    "glyme",
    "ethylene glycol",
    "catechol",
    "gallic acid",
    "ellagic acid",
)

OFF_TOPIC_TERMS: tuple[str, ...] = (
    "daydream",
    "virtual reality",
    "social media",
    "pedagogy",
    "tourism",
    "linguistics",
    "literature review of",
    "political",
    "education",
    "nursing",
    "finance",
)
