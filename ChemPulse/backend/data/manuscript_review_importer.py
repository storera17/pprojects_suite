from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import re
import uuid
from typing import Any

from backend.core.paths import storage_dir

@dataclass(frozen=True)
class ManuscriptReviewResult:
    brief_id: str
    manuscript_id: str
    title: str
    source_label: str
    report_path: str
    json_path: str
    missing_citations: int
    requested_experiments: int
    journal_transfer_notes: int
    checklist_items: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "manuscript_id": self.manuscript_id,
            "title": self.title,
            "source_label": self.source_label,
            "report_path": self.report_path,
            "json_path": self.json_path,
            "missing_citations": self.missing_citations,
            "requested_experiments": self.requested_experiments,
            "journal_transfer_notes": self.journal_transfer_notes,
            "checklist_items": self.checklist_items,
        }

def import_manuscript_review_comments(source: str | Path, source_label: str = "") -> ManuscriptReviewResult:
    text, inferred_label = _read_source(source)
    label = source_label.strip() or inferred_label
    brief = build_manuscript_review_brief(text, source_label=label)
    return save_manuscript_review_brief(brief)

def build_manuscript_review_brief(text: str, source_label: str = "reviewer comments") -> dict[str, Any]:
    normalized = _normalize(text)
    manuscript_id = _first_match(normalized, r"manuscript[:\s]+([0-9]{5,})", "unknown")
    title = _first_match(normalized, r'titled\s+"([^"]+)"', "Untitled manuscript")
    decision = "Rejected" if re.search(r"\breject(?:ed|ion)?\b|unable to accept", normalized, re.I) else "Needs response"
    reviewer_sections = _reviewer_sections(normalized)

    missing_citations = _missing_citations(normalized)
    requested_experiments = _requested_experiments(reviewer_sections)
    transfer_notes = _journal_transfer_notes(normalized)
    critical_concerns = _critical_concerns(normalized)
    checklist = _response_checklist(missing_citations, requested_experiments, transfer_notes, critical_concerns)

    return {
        "brief_id": f"ms-review-{uuid.uuid4()}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_label": source_label,
        "manuscript_id": manuscript_id,
        "title": title,
        "decision": decision,
        "reviewers": _reviewer_summaries(reviewer_sections),
        "missing_citations": missing_citations,
        "requested_experiments": requested_experiments,
        "journal_transfer_notes": transfer_notes,
        "critical_concerns": critical_concerns,
        "response_checklist": checklist,
    }

def save_manuscript_review_brief(brief: dict[str, Any]) -> ManuscriptReviewResult:
    reports_dir = storage_dir() / "reports"
    briefs_dir = storage_dir() / "manuscript-reviews"
    reports_dir.mkdir(parents=True, exist_ok=True)
    briefs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    manuscript_id = _slug(str(brief.get("manuscript_id") or "unknown"))
    brief_id = str(brief.get("brief_id") or f"ms-review-{uuid.uuid4()}")
    json_path = briefs_dir / f"manuscript-review-{timestamp}-{manuscript_id}.json"
    report_path = reports_dir / f"manuscript-review-{timestamp}-{manuscript_id}.md"

    brief = {**brief, "brief_id": brief_id, "report_path": str(report_path), "json_path": str(json_path)}
    json_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")
    report_path.write_text(render_manuscript_review_markdown(brief), encoding="utf-8")

    return ManuscriptReviewResult(
        brief_id=brief_id,
        manuscript_id=str(brief.get("manuscript_id") or "unknown"),
        title=str(brief.get("title") or ""),
        source_label=str(brief.get("source_label") or ""),
        report_path=str(report_path),
        json_path=str(json_path),
        missing_citations=len(brief.get("missing_citations") or []),
        requested_experiments=len(brief.get("requested_experiments") or []),
        journal_transfer_notes=len(brief.get("journal_transfer_notes") or []),
        checklist_items=len(brief.get("response_checklist") or []),
    )

def latest_manuscript_review_brief() -> dict[str, Any]:
    briefs_dir = storage_dir() / "manuscript-reviews"
    candidates = sorted(briefs_dir.glob("manuscript-review-*.json"), reverse=True) if briefs_dir.exists() else []
    if not candidates:
        return _empty_brief()
    try:
        payload = json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception as exc:
        payload = _empty_brief()
        payload["status"] = f"Latest manuscript-review brief could not be read: {exc}"
    return payload

def render_manuscript_review_markdown(brief: dict[str, Any]) -> str:
    lines = [
        f"# Manuscript Review Brief: {brief.get('manuscript_id', 'unknown')}",
        "",
        f"Title: {brief.get('title', 'Untitled manuscript')}",
        f"Decision: {brief.get('decision', 'Needs response')}",
        f"Source: {brief.get('source_label', 'reviewer comments')}",
        "",
        "## Missing Citations",
    ]
    lines.extend(_markdown_items(brief.get("missing_citations") or [], "citation"))
    lines.extend(["", "## Requested Experiments"])
    lines.extend(_markdown_items(brief.get("requested_experiments") or [], "experiment"))
    lines.extend(["", "## Journal Transfer Notes"])
    lines.extend(_markdown_items(brief.get("journal_transfer_notes") or [], "journal"))
    lines.extend(["", "## Response Checklist"])
    for item in brief.get("response_checklist") or []:
        lines.append(f"- [ ] {item.get('task', '')}")
    lines.append("")
    return "\n".join(lines)

def _read_source(source: str | Path) -> tuple[str, str]:
    path = Path(source).expanduser()
    if path.exists():
        return path.read_text(encoding="utf-8"), str(path)
    return str(source), "inline reviewer comments"

def _reviewer_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"\bReviewer\s+(\d+)\b", text, re.I))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[f"Reviewer {match.group(1)}"] = text[start:end].strip()
    return sections

def _reviewer_summaries(sections: dict[str, str]) -> list[dict[str, str]]:
    summaries = []
    for reviewer, section in sections.items():
        recommendation = _first_match(section, r"Recommendation:\s*(.*?)\s*(?:Please rate|Comments to the Author|$)", "Unstated")
        importance = _first_match(section, r"importance.*?\n\s*(High|Moderate|Low.*?)\s*\(", "Unstated")
        novelty = _first_match(section, r"novelty.*?\n\s*(High|Moderate|Low.*?)\s*\(", "Unstated")
        summaries.append({"reviewer": reviewer, "recommendation": recommendation.strip(), "importance": importance, "novelty": novelty})
    return summaries

def _missing_citations(text: str) -> list[dict[str, str]]:
    patterns = [
        (r"Chemical Society Reviews,\s*2026,\s*55,\s*3469-3598", "Reviewer 1 requested this broad C(sp3)-N(sp3) bond-formation review."),
        (r"JOC\s*2018,\s*83,\s*9546", "Reviewer 2 flagged prior deoxyamination of O-protected isosorbide with alkylamines."),
        (r"ACIE\s*2016,\s*55,\s*10145", "Reviewer 2 called this an important stereospecific deoxyamination reference."),
        (r"CEJ\s*2018,\s*24,\s*7410", "Reviewer 2 called this an important stereospecific deoxyamination reference."),
    ]
    citations = []
    for pattern, rationale in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            citations.append({"citation": match.group(0), "rationale": rationale, "status": "missing"})
    if re.search(r"previous work should be discussed|key references were missing|references.*No", text, re.I):
        citations.append(
            {
                "citation": "Expanded prior-work discussion",
                "rationale": "Both reviewer sentiment and the editor emphasized novelty relative to earlier work.",
                "status": "narrative revision",
            }
        )
    return _dedupe(citations, "citation")

def _requested_experiments(sections: dict[str, str]) -> list[dict[str, str]]:
    text = "\n".join(sections.values())
    requests = [
        ("Ammonia or ammonium salts", r"ammonia or ammonium salts", "Demonstrate primary-amine synthesis from ammonia/ammonium nucleophiles."),
        ("Primary amines", r"reaction of primary amines", "Add examples using primary amines as nucleophiles."),
        ("Acyclic aliphatic secondary alcohols", r"acyclic aliphatic secondary alcohols", "Test less constrained secondary alcohol substrates."),
        ("Unactivated diols", r"unactivated diols", "Demonstrate selectivity or compatibility with unactivated diols."),
        ("Unbiased enantiopure substrates", r"unbiased enantiopure substrates", "Address Reviewer 2's concern about biased substrates."),
    ]
    items = []
    for label, pattern, request in requests:
        if re.search(pattern, text, re.I):
            items.append({"experiment": label, "request": request, "status": "planned"})
    return items

def _journal_transfer_notes(text: str) -> list[dict[str, str]]:
    notes = []
    if re.search(r"Advanced\s+Synthesis\s+&\s+Catalysis", text, re.I):
        notes.append({"journal": "Advanced Synthesis & Catalysis", "note": "Wiley recommended transfer option; impact factor listed as 4."})
    if re.search(r"ChemistryEurope", text, re.I):
        notes.append({"journal": "ChemistryEurope", "note": "Wiley recommended fully open-access transfer option."})
    if re.search(r"\bEurJOC\b", text, re.I):
        notes.append({"journal": "EurJOC", "note": "Reviewer 2 named EurJOC as an expected venue."})
    if re.search(r"Org\.?\s*Lett|Organic Letters|\bOL template\b", text, re.I):
        notes.append({"journal": "Organic Letters", "note": "Internal thread pivoted toward an OL resubmission with a short communication format."})
    if re.search(r"start manuscript transfer|transfer your revised manuscript", text, re.I):
        notes.append({"journal": "Wiley transfer workflow", "note": "Transfer can carry files, supporting documentation, and peer-review reports into a new draft."})
    return _dedupe(notes, "journal")

def _critical_concerns(text: str) -> list[dict[str, str]]:
    concerns = [
        ("Novelty versus OL reference 37", r"follow-up work.*OL.*reference 37|slightly different promoter system"),
        ("Biased substrate set", r"biased substrates|tailored substrates"),
        ("Scale-up/PFAS concern", r"PBSF is a PFAS|large amounts of reagents|required"),
        ("Large-scale synthetic utility", r"transposition of this process on large scale questionable|Alternative strategies"),
    ]
    return [{"concern": label, "status": "needs response"} for label, pattern in concerns if re.search(pattern, text, re.I)]

def _response_checklist(
    citations: list[dict[str, str]],
    experiments: list[dict[str, str]],
    transfer_notes: list[dict[str, str]],
    concerns: list[dict[str, str]],
) -> list[dict[str, str]]:
    tasks = []
    tasks.extend({"task": f"Add or discuss citation: {item['citation']}", "category": "citation"} for item in citations)
    tasks.extend({"task": f"Plan response experiment: {item['request']}", "category": "experiment"} for item in experiments)
    tasks.extend({"task": f"Draft rebuttal/cover-letter language for {item['concern']}.", "category": "response"} for item in concerns)
    if transfer_notes:
        tasks.append({"task": "Choose journal path: Wiley transfer option, EurJOC, or Organic Letters resubmission.", "category": "journal"})
    tasks.append({"task": "Prepare a point-by-point response table before resubmission.", "category": "response"})
    return tasks

def _markdown_items(items: list[dict[str, str]], primary: str) -> list[str]:
    if not items:
        return ["- None detected."]
    lines = []
    for item in items:
        label = item.get(primary) or item.get("journal") or item.get("experiment") or item.get("concern") or "Item"
        detail = item.get("rationale") or item.get("request") or item.get("note") or item.get("status") or ""
        lines.append(f"- {label}: {detail}")
    return lines

def _first_match(text: str, pattern: str, default: str) -> str:
    match = re.search(pattern, text, re.I | re.S)
    return match.group(1).strip() if match else default

def _normalize(text: str) -> str:
    return re.sub(r"\r\n?", "\n", text or "").replace("C(sp³)", "C(sp3)").replace("N(sp³)", "N(sp3)")

def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "unknown"

def _dedupe(items: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    seen = set()
    unique = []
    for item in items:
        marker = item.get(key, "").lower()
        if marker and marker not in seen:
            seen.add(marker)
            unique.append(item)
    return unique

def _empty_brief() -> dict[str, Any]:
    return {
        "brief_id": "",
        "status": "No manuscript-review brief has been generated yet.",
        "manuscript_id": "",
        "title": "",
        "decision": "",
        "missing_citations": [],
        "requested_experiments": [],
        "journal_transfer_notes": [],
        "critical_concerns": [],
        "response_checklist": [],
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Import reviewer comments into a ChemPulse manuscript-review brief.")
    parser.add_argument("source", help="Reviewer-comment text file path, or inline reviewer-comment text.")
    parser.add_argument("--source-label", default="", help="Human-readable source label for the generated report.")
    args = parser.parse_args()
    result = import_manuscript_review_comments(args.source, source_label=args.source_label)
    print(json.dumps(result.as_dict(), indent=2))

if __name__ == "__main__":
    main()
