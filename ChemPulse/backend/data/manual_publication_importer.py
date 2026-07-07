from __future__ import annotations

import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

import requests

from backend.data.core_publication_repository import CorePublicationRepository

SUPPORTED_EXTENSIONS = {".csv", ".json", ".jsonl"}
DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://[^\s<>\"]+", re.IGNORECASE)
REQUEST_TIMEOUT_SECONDS = 15

@dataclass
class ManualImportResult:
    scanned_files: int
    parsed_records: int
    inserted: int
    updated: int
    skipped: int
    report_path: str
    errors: list[str]
    import_type: str = "file"
    normalized_items: list[dict[str, str]] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scanned_files": self.scanned_files,
            "parsed_records": self.parsed_records,
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "report_path": self.report_path,
            "errors": self.errors,
            "import_type": self.import_type,
            "normalized_items": self.normalized_items or [],
        }