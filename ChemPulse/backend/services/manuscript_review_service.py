from __future__ import annotations

from typing import Any

from backend.data.manuscript_review_importer import latest_manuscript_review_brief


class ManuscriptReviewService:
    @staticmethod
    def latest_brief() -> dict[str, Any]:
        brief = latest_manuscript_review_brief()
        citations = brief.get("missing_citations") or []
        experiments = brief.get("requested_experiments") or []
        transfers = brief.get("journal_transfer_notes") or []
        checklist = brief.get("response_checklist") or []
        return {
            "brief": brief,
            "summary": {
                "manuscript_id": brief.get("manuscript_id", ""),
                "title": brief.get("title", ""),
                "decision": brief.get("decision", ""),
                "source_label": brief.get("source_label", ""),
                "report_path": brief.get("report_path", ""),
                "citation_count": len(citations),
                "experiment_count": len(experiments),
                "transfer_count": len(transfers),
                "checklist_count": len(checklist),
            },
            "missing_citations": citations,
            "requested_experiments": experiments,
            "journal_transfer_notes": transfers,
            "response_checklist": checklist,
            "metadata": {
                "record_count": len(checklist),
                "source": "storage/manuscript-reviews",
                "service": "ManuscriptReviewService.latest_brief",
                "empty_state_reason": "" if checklist else "No manuscript-review brief has been generated yet.",
            },
        }
