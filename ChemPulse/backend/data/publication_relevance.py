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

def publication_relevance(title: str, abstract: str = "", journal: str = "", topics: str = "") -> tuple[int, str]:
    text = f"{title} {abstract} {journal} {topics}".lower()
    focus_hits = _term_hits(text, FOCUS_TERMS)
    context_hits = _term_hits(text, CHEMISTRY_CONTEXT_TERMS)
    scaffold_hits = _term_hits(text, SUPPORTING_SCAFFOLD_TERMS)
    off_topic_hits = _term_hits(text, OFF_TOPIC_TERMS)

    score = focus_hits * 28 + min(context_hits, 4) * 12 + scaffold_hits * 14
    if focus_hits and context_hits:
        score += 16
    if focus_hits >= 2:
        score += 12
    score -= off_topic_hits * 45
    score = max(0, min(score, 100))

    if score >= HIGH_RELEVANCE_THRESHOLD:
        return score, "High relevance"
    if score >= MEDIUM_RELEVANCE_THRESHOLD:
        return score, "Medium relevance"
    if score >= LOW_RELEVANCE_THRESHOLD:
        return score, "Low relevance"
    return score, "Off-topic"

def is_ingestion_relevant(publication: dict, min_score: int = DEFAULT_MIN_INGESTION_RELEVANCE_SCORE) -> bool:
    topics = publication.get("topics") or []
    topics_text = ", ".join(str(topic) for topic in topics) if isinstance(topics, list) else str(topics)
    score, _ = publication_relevance(
        str(publication.get("title") or ""),
        str(publication.get("abstract") or ""),
        str(publication.get("journal") or ""),
        topics_text,
    )
    return score >= min_score and publication_matches_focus(
        str(publication.get("title") or ""),
        str(publication.get("abstract") or ""),
        str(publication.get("journal") or ""),
        topics_text,
    )

def publication_matches_focus(title: str, abstract: str = "", journal: str = "", topics: str = "") -> bool:
    text = f"{title} {abstract} {journal} {topics}".lower()
    return _term_hits(text, FOCUS_TERMS) > 0

def _term_hits(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if term in text)

