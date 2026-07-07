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
