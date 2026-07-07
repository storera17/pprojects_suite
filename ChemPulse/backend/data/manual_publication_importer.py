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

def import_quick_publication_leads(leads: Iterable[dict[str, Any]]) -> ManualImportResult:
    normalized_items: list[dict[str, Any]] = []
    warnings: list[str] = []
    skipped = 0
    seen_publications: set[str] = set()
    duplicate_sources: list[str] = []

    for lead in leads:
        raw_source = str(lead.get("raw_source") or "").strip()
        if not raw_source:
            skipped += 1
            warnings.append("Skipped an empty quick-import lead.")
            continue
        provenance = lead.get("provenance")
        try:
            normalized = normalize_quick_publication_lead(raw_source, provenance=provenance)
        except Exception as exc:
            skipped += 1
            warnings.append(f"Skipped quick-import lead `{raw_source}`: {exc}")
            continue
        warnings.extend(str(item) for item in normalized.get("warnings", []))
        publication = normalized.get("publication")
        if not publication:
            skipped += 1
            continue
        publication_key = str(
            publication.get("core_id")
            or normalized.get("canonical_source")
            or publication.get("doi")
            or publication.get("source_url")
            or raw_source
        ).lower()
        if publication_key in seen_publications:
            skipped += 1
            duplicate_sources.append(raw_source)
            continue
        seen_publications.add(publication_key)
        normalized_items.append(normalized)

    if duplicate_sources:
        warnings.append(f"Skipped {len(duplicate_sources)} duplicate quick-import lead(s) in this batch.")

    publications = [item["publication"] for item in normalized_items if item.get("publication")]
    run_id = f"quick-{uuid.uuid4()}"
    query = f"quick import batch: {len(publications)} unique lead(s)"
    CorePublicationRepository.start_run(run_id, query, len(publications), max(len(publications), 1))
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
            "quick_import_batch": normalized_items,
            "scanned_files": 0,
            "skipped": skipped,
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
            "quick_import_batch": normalized_items,
            "scanned_files": 0,
            "skipped": skipped + len(publications),
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

def normalize_quick_publication_lead(raw_source: str, provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    source = raw_source.strip().strip('"')
    decoded = _decode_repeatedly(source)
    doi = _extract_doi(decoded)
    url = _extract_url(decoded)
    warnings: list[str] = []
    metadata: dict[str, Any] = {}
    metadata_source = ""

    if doi:
        try:
            metadata = _fetch_crossref_metadata(doi)
            metadata_source = "Crossref"
        except Exception as exc:
            warnings.append(f"Crossref metadata lookup failed for DOI {doi}: {exc}")
            metadata = {"title": f"External publication lead {doi}", "doi": doi, "url": f"https://doi.org/{doi}"}
            metadata_source = "DOI fallback"
    elif url:
        try:
            metadata = _fetch_url_metadata(url)
            metadata_source = "page metadata"
            doi = _clean_doi(str(metadata.get("doi") or "")) or _extract_doi(json.dumps(metadata))
            if doi and not metadata.get("doi"):
                metadata["doi"] = doi
        except Exception as exc:
            warnings.append(f"URL metadata lookup failed for {url}: {exc}")
            metadata = {"title": _readable_title_from_url(url), "url": url}
            metadata_source = "URL fallback"
    else:
        raise ValueError("Paste a DOI, DOI URL, email link, or article URL.")

    normalized_provenance = _normalize_provenance(provenance, lead_source=source)
    publication = _publication_from_metadata(
        metadata,
        raw_source=source,
        doi=doi,
        url=url,
        metadata_source=metadata_source,
        provenance=normalized_provenance,
    )
    if not publication.get("title"):
        raise ValueError("Could not find a publication title in that lead.")

    return {
        "raw_source": source,
        "canonical_source": publication.get("doi") or publication.get("source_url") or source,
        "input_kind": "doi" if doi else "url",
        "metadata_source": metadata_source,
        "provenance": normalized_provenance,
        "warnings": warnings,
        "publication": publication,
    }

def extract_quick_publication_leads(value: str) -> list[str]:
    text = value.strip()
    if not text:
        return []

    candidates: list[str] = []
    seen: set[str] = set()
    texts = [text, html.unescape(text)]
    for candidate_text in list(texts):
        decoded = _decode_repeatedly(candidate_text)
        if decoded not in texts:
            texts.append(decoded)

    for candidate_text in texts:
        doi = _extract_doi(candidate_text)
        if doi and doi not in seen:
            seen.add(doi)
            candidates.append(doi)
        for match in URL_PATTERN.finditer(candidate_text):
            url = match.group(0).rstrip(").,;]'\"")
            if not _looks_like_quick_lead(url):
                continue
            if url in seen:
                continue
            seen.add(url)
            candidates.append(url)
    return candidates

def write_manual_import_report(result: dict[str, Any]) -> Path:
    from backend.config import get_config

    config = get_config()
    report_dir = config.storage_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_path = report_dir / f"manual-publication-import-{timestamp}-{result['run_id']}.md"
    lines = [
        "# ChemPulse Manual Publication Import",
        "",
        f"- Run ID: `{result['run_id']}`",
        f"- Status: `{result['status']}`",
        f"- Source: `{result['query']}`",
        f"- Files scanned: `{result.get('scanned_files', 0)}`",
        f"- Parsed records: `{result.get('downloaded', 0)}`",
        f"- Inserted: `{result.get('inserted', 0)}`",
        f"- Updated: `{result.get('updated', 0)}`",
        f"- Skipped rows: `{result.get('skipped', 0)}`",
        "",
        "## New Publications",
        "",
        _format_items(result.get("inserted_items", [])),
        "",
        "## Updated Publications",
        "",
        _format_items(result.get("updated_items", [])),
    ]
    if result.get("quick_import"):
        quick = result["quick_import"]
        publication = quick.get("publication", {})
        lines.extend(
            [
                "",
                "## Quick Import Normalization",
                "",
                f"- Input kind: `{quick.get('input_kind', 'unknown')}`",
                f"- Metadata source: `{quick.get('metadata_source', 'unknown')}`",
                f"- Normalized DOI: `{publication.get('doi') or 'n/a'}`",
                f"- Normalized URL: `{publication.get('source_url') or publication.get('full_text_url') or 'n/a'}`",
                f"- Title: {publication.get('title', 'Untitled')}",
                f"- Journal: {publication.get('journal') or 'Unknown source'}",
                f"- Year: `{publication.get('year_published') or 'n/a'}`",
                f"- Authors: {', '.join(publication.get('authors') or []) or 'Unknown authors'}",
                f"- Topics: {', '.join(publication.get('topics') or []) or 'No topics found'}",
            ]
        )
        provenance = quick.get("provenance") or publication.get("raw", {}).get("provenance", {})
        if provenance:
            lines.extend(
                [
                    "",
                    "## Quick Import Provenance",
                    "",
                    f"- Channel: `{provenance.get('channel') or 'manual'}`",
                    f"- Provider: `{provenance.get('provider') or 'Unknown'}`",
                    f"- Query: `{provenance.get('query') or 'n/a'}`",
                    f"- Sender: {provenance.get('sender') or 'Unknown sender'}",
                    f"- Subject: {provenance.get('subject') or 'Unknown subject'}",
                    f"- Received at: `{provenance.get('received_at') or 'n/a'}`",
                    f"- Message ID: `{provenance.get('message_id') or 'n/a'}`",
                    f"- Lead source: `{provenance.get('lead_source') or quick.get('raw_source') or 'n/a'}`",
                ]
            )
    if result.get("quick_import_batch"):
        batch_items = list(result["quick_import_batch"])
        lines.extend(
            [
                "",
                "## Quick Import Batch",
                "",
                f"- Unique leads imported: `{len(batch_items)}`",
                f"- Duplicate/empty leads skipped: `{result.get('skipped', 0)}`",
            ]
        )
        for index, quick in enumerate(batch_items[:25], start=1):
            publication = quick.get("publication", {})
            provenance = quick.get("provenance") or publication.get("raw", {}).get("provenance", {})
            lines.extend(
                [
                    "",
                    f"### Lead {index}",
                    "",
                    f"- Title: {publication.get('title', 'Untitled')}",
                    f"- DOI: `{publication.get('doi') or 'n/a'}`",
                    f"- Journal: {publication.get('journal') or 'Unknown source'}",
                    f"- Sender: {provenance.get('sender') or 'Unknown sender'}",
                    f"- Subject: {provenance.get('subject') or 'Unknown subject'}",
                    f"- Received at: `{provenance.get('received_at') or 'n/a'}`",
                    f"- Message ID: `{provenance.get('message_id') or 'n/a'}`",
                    f"- Lead source: `{provenance.get('lead_source') or quick.get('raw_source') or 'n/a'}`",
                ]
            )
        if len(batch_items) > 25:
            lines.extend(["", f"- ...and {len(batch_items) - 25} more quick-import lead(s)."])
    if result.get("errors"):
        lines.extend(["", "## Import Warnings", ""])
        lines.extend(f"- {error}" for error in result["errors"])
    if result.get("error"):
        lines.extend(["", "## Error", "", str(result["error"])])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path

def _iter_import_files(path: Path, recursive: bool) -> Iterable[Path]:
    if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
        yield path
        return
    if not path.exists():
        raise FileNotFoundError(f"Import path does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Import path must be a supported file or folder: {path}")
    iterator = path.rglob("*") if recursive else path.glob("*")
    for candidate in sorted(iterator):
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield candidate

def _read_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("publications", "records", "items", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [data]
    return []

def _normalize_row(row: dict[str, Any], file_path: Path, index: int) -> dict[str, Any] | None:
    title = _pick(row, "title", "name", "publication_title", "article_title")
    if not title:
        return None

    doi = _pick(row, "doi", "DOI")
    core_id = _pick(row, "core_id", "id", "publication_id")
    if not core_id:
        stable_key = doi or f"{file_path.resolve()}:{index}:{title}"
        core_id = f"manual:{stable_key}".lower()

    authors = _list_value(_pick(row, "authors", "author", "creators", "contributors"))
    topics = _list_value(_pick(row, "topics", "keywords", "tags", "subjects"))
    year = _int_value(_pick(row, "year_published", "year", "publication_year", "published_year"))
    published_date = _pick(row, "published_date", "date", "published", "publication_date")
    journal = _pick(row, "journal", "source", "container_title", "publication", "venue")
    abstract = _pick(row, "abstract", "summary", "description")
    url = _pick(row, "full_text_url", "url", "link", "source_url")

    return {
        "core_id": str(core_id),
        "title": str(title),
        "doi": doi,
        "year_published": year,
        "published_date": published_date,
        "authors": authors,
        "journal": journal,
        "abstract": abstract,
        "topics": topics,
        "full_text_url": url,
        "source_url": url,
        "raw": {"source": "manual", "file": str(file_path), "row": row},
    }

def _looks_like_quick_lead(value: str) -> bool:
    text = value.strip().strip('"')
    if not text:
        return False
    if DOI_PATTERN.search(_decode_repeatedly(text)):
        return True
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"}

def _decode_repeatedly(value: str, rounds: int = 3) -> str:
    decoded = value
    for _ in range(rounds):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded

def _extract_doi(value: str) -> str:
    match = DOI_PATTERN.search(value)
    return _clean_doi(match.group(0)) if match else ""

def _clean_doi(value: str) -> str:
    return value.strip().rstrip(").,;]'\"").lower()

def _extract_url(value: str) -> str:
    match = URL_PATTERN.search(value)
    if not match:
        return ""
    return match.group(0).rstrip(").,;]'\"")

def _fetch_crossref_metadata(doi: str) -> dict[str, Any]:
    url = f"https://api.crossref.org/works/{requests.utils.quote(doi, safe='')}"
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": "ChemPulse quick publication import (mailto:local@chempulse.invalid)"},
    )
    response.raise_for_status()
    message = response.json().get("message", {})
    authors = []
    for author in message.get("author", []) or []:
        name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
        if name:
            authors.append(name)
    published = _crossref_date(message, "published-print") or _crossref_date(message, "published-online") or _crossref_date(message, "issued")
    year = _int_value(published)
    abstract = _strip_html(message.get("abstract", ""))
    return {
        "title": _first_text(message.get("title")),
        "doi": _clean_doi(str(message.get("DOI") or doi)),
        "year_published": year,
        "published_date": published,
        "authors": authors,
        "journal": _first_text(message.get("container-title")) or _first_text(message.get("short-container-title")),
        "abstract": abstract,
        "topics": _list_value(message.get("subject")),
        "url": message.get("URL") or f"https://doi.org/{doi}",
        "raw": message,
    }

def _fetch_url_metadata(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": "ChemPulse quick publication import"})
    response.raise_for_status()
    parser = _PublicationMetadataParser()
    parser.feed(response.text[:500_000])
    data = parser.metadata()
    data["url"] = url
    data["raw"] = {"url": url, "metadata": data.copy()}
    return data

def _publication_from_metadata(
    metadata: dict[str, Any],
    raw_source: str,
    doi: str,
    url: str,
    metadata_source: str,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_doi = _clean_doi(str(metadata.get("doi") or doi or ""))
    source_url = str(metadata.get("url") or url or (f"https://doi.org/{normalized_doi}" if normalized_doi else ""))
    title = str(metadata.get("title") or "").strip()
    core_id = f"manual:doi:{normalized_doi}" if normalized_doi else f"manual:url:{hashlib.sha256(source_url.encode('utf-8')).hexdigest()[:16]}"
    abstract = _strip_html(str(metadata.get("abstract") or metadata.get("description") or ""))
    topics = _list_value(metadata.get("topics") or metadata.get("keywords"))
    if not topics:
        topics = _infer_topics(title, abstract)
    return {
        "core_id": core_id.lower(),
        "title": title,
        "doi": normalized_doi or None,
        "year_published": _int_value(metadata.get("year_published") or metadata.get("year") or metadata.get("published_date")),
        "published_date": metadata.get("published_date"),
        "authors": _list_value(metadata.get("authors")),
        "journal": metadata.get("journal") or metadata.get("source") or "External literature lead",
        "abstract": abstract,
        "topics": topics,
        "full_text_url": source_url,
        "source_url": source_url,
        "raw": {
            "source": "quick-import",
            "raw_source": raw_source,
            "metadata_source": metadata_source,
            "provenance": provenance or {},
            "metadata": metadata.get("raw", metadata),
        },
    }

def _normalize_provenance(provenance: dict[str, Any] | None, lead_source: str) -> dict[str, str]:
    if not provenance:
        return {}

    normalized: dict[str, str] = {}
    for key, value in provenance.items():
        if value in (None, ""):
            continue
        normalized[str(key)] = str(value)
    normalized.setdefault("lead_source", lead_source)
    if normalized.get("channel") == "gmail":
        normalized.setdefault("provider", "Gmail")
    return normalized

def _crossref_date(message: dict[str, Any], key: str) -> str:
    parts = ((message.get(key) or {}).get("date-parts") or [[]])[0]
    if not parts:
        return ""
    padded = [str(part).zfill(2) for part in parts]
    return "-".join([str(parts[0]), *padded[1:]])

def _first_text(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value).strip() if value not in (None, "") else ""

def _strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value))).strip()

def _infer_topics(title: str, abstract: str) -> list[str]:
    text = f"{title} {abstract}".lower()
    candidates = [
        ("Suzuki-Miyaura coupling", "suzuki"),
        ("NHC precursors", "nhc"),
        ("azolium salts", "azolium"),
        ("dicationic salts", "dicationic"),
        ("catalysis", "catal"),
        ("synthesis", "synthesis"),
    ]
    return [label for label, needle in candidates if needle in text][:5]

def _readable_title_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("-", " ").replace("_", " ")
    return path.title() or parsed.netloc or "External literature lead"

class _PublicationMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, list[str]] = {}
        self.title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() != "meta":
            return
        name = (attrs_map.get("name") or attrs_map.get("property") or "").lower()
        content = attrs_map.get("content", "").strip()
        if name and content:
            self.meta.setdefault(name, []).append(content)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and data.strip():
            self.title_parts.append(data.strip())

    def metadata(self) -> dict[str, Any]:
        title = self._pick("citation_title", "dc.title", "og:title") or " ".join(self.title_parts)
        return {
            "title": title,
            "doi": self._pick("citation_doi", "dc.identifier", "dc.identifier.doi"),
            "published_date": self._pick("citation_publication_date", "citation_date", "article:published_time"),
            "year_published": self._pick("citation_year"),
            "authors": self.meta.get("citation_author", []),
            "journal": self._pick("citation_journal_title", "citation_conference_title", "og:site_name"),
            "abstract": self._pick("description", "dc.description", "og:description"),
            "topics": self._pick("citation_keywords", "keywords"),
        }

    def _pick(self, *keys: str) -> str:
        for key in keys:
            values = self.meta.get(key)
            if values:
                return values[0]
        return ""

def _pick(row: dict[str, Any], *keys: str) -> Any:
    lower_map = {str(key).lower(): value for key, value in row.items()}
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
        value = lower_map.get(key.lower())
        if value not in (None, ""):
            return value
    return None

def _list_value(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value)
    separator = ";" if ";" in text else ","
    return [item.strip() for item in text.split(separator) if item.strip()]

def _int_value(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value)[:4])
    except ValueError:
        return None

def _format_items(items: list[dict[str, str]], limit: int = 25) -> str:
    if not items:
        return "None."
    lines = []
    for item in items[:limit]:
        title = item.get("title", "Untitled")
        journal = item.get("journal", "Unknown source")
        year = item.get("year", "n/a")
        doi = item.get("doi", "")
        suffix = f" DOI: `{doi}`" if doi else ""
        lines.append(f"- {title} ({journal}, {year}).{suffix}")
    if len(items) > limit:
        lines.append(f"- ...and {len(items) - limit} more.")
    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser(description="Import manual publication CSV, JSON, or JSONL files into ChemPulse.")
    parser.add_argument("path", help="Publication file or folder to import.")
    parser.add_argument("--no-recursive", action="store_true", help="Only scan the top level when importing a folder.")
    args = parser.parse_args()
    result = import_manual_publications(args.path, recursive=not args.no_recursive)
    print(json.dumps(result.as_dict(), indent=2))

if __name__ == "__main__":
    main()