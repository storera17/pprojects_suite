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
        
def import_manual_publications(path: str | Path, recursive: bool = True) -> ManualImportResult:
    raw_source = str(path).strip()
    if _looks_like_quick_lead(raw_source):
        return import_quick_publication_lead(raw_source)

    source_path = Path(path).expanduser()
    files = list(_iter_import_files(source_path, recursive=recursive))
    errors: list[str] = []
    publications: list[dict[str, Any]] = []
    skipped = 0

    for file_path in files:
        try:
            rows = _read_file(file_path)
        except Exception as exc:
            errors.append(f"{file_path}: {exc}")
            continue

        for index, row in enumerate(rows, start=1):
            publication = _normalize_row(row, file_path, index)
            if publication is None:
                skipped += 1
                continue
            publications.append(publication)

    run_id = f"manual-{uuid.uuid4()}"
    query = f"manual import: {source_path}"
    CorePublicationRepository.start_run(run_id, query, len(publications), max(len(publications), 1))
    try:
        counts = CorePublicationRepository.upsert_publications(publications, query)
        CorePublicationRepository.finish_run(run_id, "succeeded", counts["inserted"], counts["updated"])
        result = {
            "run_id": run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": "succeeded",
            "query": query,
            "downloaded": len(publications),
            "inserted": counts["inserted"],
            "updated": counts["updated"],
            "inserted_items": counts.get("inserted_items", []),
            "updated_items": counts.get("updated_items", []),
            "error": "",
            "source": "manual",
            "scanned_files": len(files),
            "skipped": skipped,
            "errors": errors,
        }
    except Exception as exc:
        CorePublicationRepository.finish_run(run_id, "failed", 0, 0, str(exc))
        result = {
            "run_id": run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "query": query,
            "downloaded": len(publications),
            "inserted": 0,
            "updated": 0,
            "inserted_items": [],
            "updated_items": [],
            "error": str(exc),
            "source": "manual",
            "scanned_files": len(files),
            "skipped": skipped,
            "errors": errors,
        }

    report_path = write_manual_import_report(result)
    return ManualImportResult(
        scanned_files=len(files),
        parsed_records=len(publications),
        inserted=int(result["inserted"]),
        updated=int(result["updated"]),
        skipped=skipped,
        report_path=str(report_path),
        errors=errors + ([str(result["error"])] if result.get("error") else []),
        import_type="file",
        normalized_items=list(result.get("inserted_items", [])) + list(result.get("updated_items", [])),
    )

def import_quick_publication_lead(raw_source: str, provenance: dict[str, Any] | None = None) -> ManualImportResult:
    normalized = normalize_quick_publication_lead(raw_source, provenance=provenance)
    publications = [normalized["publication"]] if normalized.get("publication") else []
    warnings = list(normalized.get("warnings", []))
    run_id = f"quick-{uuid.uuid4()}"
    query = f"quick import: {normalized.get('canonical_source') or raw_source}"
    CorePublicationRepository.start_run(run_id, query, len(publications), 1)
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        counts = CorePublicationRepository.upsert_publications(publications, query)
        CorePublicationRepository.finish_run(run_id, "succeeded", counts["inserted"], counts["updated"])
        result = {
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": "succeeded",
            "query": query,
            "downloaded": len(publications),
            "inserted": counts["inserted"],
            "updated": counts["updated"],
            "inserted_items": counts.get("inserted_items", []),
            "updated_items": counts.get("updated_items", []),
            "error": "",
            "source": "quick",
            "quick_import": normalized,
            "scanned_files": 0,
            "skipped": 0 if publications else 1,
            "errors": warnings,
        }
    except Exception as exc:
        CorePublicationRepository.finish_run(run_id, "failed", 0, 0, str(exc))
        result = {
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "query": query,
            "downloaded": len(publications),
            "inserted": 0,
            "updated": 0,
            "inserted_items": [],
            "updated_items": [],
            "error": str(exc),
            "source": "quick",
            "quick_import": normalized,
            "scanned_files": 0,
            "skipped": len(publications),
            "errors": warnings,
        }

    report_path = write_manual_import_report(result)
    return ManualImportResult(
        scanned_files=0,
        parsed_records=len(publications),
        inserted=int(result["inserted"]),
        updated=int(result["updated"]),
        skipped=int(result["skipped"]),
        report_path=str(report_path),
        errors=warnings + ([str(result["error"])] if result.get("error") else []),
        import_type="quick",
        normalized_items=list(result.get("inserted_items", [])) + list(result.get("updated_items", [])),
    )
