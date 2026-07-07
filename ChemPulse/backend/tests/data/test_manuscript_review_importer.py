from __future__ import annotations

from backend.data.manuscript_review_importer import (
    build_manuscript_review_brief,
    import_manuscript_review_comments,
    latest_manuscript_review_brief,
)
from backend.services.manuscript_review_service import ManuscriptReviewService


THREAD_EXCERPT = """
Dear Professor Byoungmoo Kim,

Thank you for submitting manuscript 7227176, titled "Direct Stereospecific Deoxy-Amination of Alcohols Enabled by Li-Mediated SuFEx".
Unfortunately, we are unable to accept your manuscript.

Reviewer 1
Recommendation:
Minor Revision
Comments to the Author
Issues need to be addressed:
1. Previous work should be discussed in detail in the introduction.
2. The use of ammonia or ammonium salts as nitrogen nucleophile for the synthesis of primary amines should be demonstrated.
3. The reaction of primary amines should be demonstrated.
4. How about the reaction of acyclic aliphatic secondary alcohols?
5. The reaction of unactivated diols should be demonstrated.
6. A review on C(sp3)-N(sp3) bond formation should be cited: Chemical Society Reviews, 2026, 55, 3469-3598.

Reviewer 2
Recommendation:
Reject
Are the references up-to-date, relevant, and comprehensive, including major recent works?
No
If you believe the manuscript is not a good fit for this journal, in which journal(s) would you expect to read it?
EurJOC
Comments to the Author
This represents a follow-up work by the authors recently published in OL (reference 37), using a slightly different promoter system.
Could unbiased enantiopure substrates be used to for the reaction?
Key references were missing: JOC 2018, 83, 9546; ACIE 2016, 55, 10145 and CEJ 2018, 24, 7410.
The large amounts of reagents required and the fact that PBSF is a PFAS would make the transposition of this process on large scale questionable.

We recommend these journals for your manuscript:
Advanced Synthesis & Catalysis
ChemistryEurope
Start manuscript transfer

Internal follow-up: Let's submit to Org. Lett. Convert the JACS manuscript into OL template.
"""


def test_build_manuscript_review_brief_extracts_response_buckets() -> None:
    brief = build_manuscript_review_brief(THREAD_EXCERPT, source_label="May 22 thread")

    citation_labels = {item["citation"] for item in brief["missing_citations"]}
    experiment_labels = {item["experiment"] for item in brief["requested_experiments"]}
    transfer_labels = {item["journal"] for item in brief["journal_transfer_notes"]}
    checklist_tasks = "\n".join(item["task"] for item in brief["response_checklist"])

    assert brief["manuscript_id"] == "7227176"
    assert brief["decision"] == "Rejected"
    assert "Chemical Society Reviews, 2026, 55, 3469-3598" in citation_labels
    assert "JOC 2018, 83, 9546" in citation_labels
    assert "Unbiased enantiopure substrates" in experiment_labels
    assert "Organic Letters" in transfer_labels
    assert "PFAS" in checklist_tasks


def test_import_manuscript_review_comments_saves_latest_brief(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "storage"))
    source_path = tmp_path / "reviewer-comments.txt"
    source_path.write_text(THREAD_EXCERPT, encoding="utf-8")

    result = import_manuscript_review_comments(source_path, source_label="Decision on manuscript: 7227176")
    latest = latest_manuscript_review_brief()
    service_payload = ManuscriptReviewService.latest_brief()

    assert result.report_path.endswith(".md")
    assert result.missing_citations >= 5
    assert latest["manuscript_id"] == "7227176"
    assert service_payload["summary"]["checklist_count"] == result.checklist_items
    assert service_payload["requested_experiments"]
