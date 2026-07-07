from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from backend.config import get_config
from backend.data.core_publication_repository import ensure_core_ingestion_schema
from backend.data.db import get_connection, get_db_path
from backend.data.schemas import GOLD_SCHEMA_SQL

@dataclass(frozen=True)
class ScaffoldTerm:
    name: str
    category: str

@dataclass(frozen=True)
class ScaffoldMatchResult:
    scaffold_terms: int
    publications_scanned: int
    matched_scaffolds: int
    updated_scaffolds: int
    galaxy_points: int
    report_path: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "scaffold_terms": self.scaffold_terms,
            "publications_scanned": self.publications_scanned,
            "matched_scaffolds": self.matched_scaffolds,
            "updated_scaffolds": self.updated_scaffolds,
            "galaxy_points": self.galaxy_points,
            "report_path": self.report_path,
        }

def default_scaffold_list_path() -> Path:
    return Path.home() / "Desktop" / "scaffolds.txt"

def refresh_scaffold_matches(scaffold_list_path: str | Path | None = None) -> ScaffoldMatchResult:
    path = Path(scaffold_list_path) if scaffold_list_path else default_scaffold_list_path()
    scaffold_terms = _load_scaffold_entries(path)
    _initialize_gold_schema_with_retry()
    ensure_core_ingestion_schema()

    with _get_connection_with_retry(read_only=True) as con:
        publications = con.execute(
            """
            SELECT
                core_id, title, doi, journal, abstract, topics_json, year_published, raw_json
            FROM bronze_core_publications
            """
        ).fetchall()

    matches: dict[str, dict[str, Any]] = {}
    publication_texts = [(row, _publication_text(row)) for row in publications]
    for term in scaffold_terms:
        aliases = _aliases_for_scaffold(term.name)
        pattern = _alias_pattern(aliases)
        for row, text in publication_texts:
            if not pattern.search(text):
                continue
            entry = matches.setdefault(
                term.name,
                {
                    "scaffold": term.name,
                    "category": term.category,
                    "evidence_count": 0,
                    "representative_doi": "",
                    "journals": Counter(),
                    "top_funder": "Publication evidence",
                    "total_funding": 0.0,
                    "core_ids": set(),
                },
            )
            core_id = str(row[0])
            if core_id in entry["core_ids"]:
                continue
            entry["core_ids"].add(core_id)
            entry["evidence_count"] += 1
            if not entry["representative_doi"] and row[2]:
                entry["representative_doi"] = str(row[2])
            source = _publication_source(row)
            if source:
                entry["journals"][source] += 1

    with _get_connection_with_retry(read_only=False) as con:
        ordered_matches = sorted(matches.values(), key=lambda item: (-item["evidence_count"], item["scaffold"]))
        if ordered_matches:
            matched_names = [item["scaffold"] for item in ordered_matches]
            placeholders = ", ".join(["?"] * len(matched_names))
            con.execute(f"DELETE FROM gold_scaffold_stats WHERE scaffold NOT IN ({placeholders})", matched_names)
            con.execute(f"DELETE FROM gold_galaxy_points WHERE scaffold NOT IN ({placeholders})", matched_names)

        updated = 0
        points = 0
        for index, scaffold in enumerate(ordered_matches):
            top_journal = scaffold["journals"].most_common(1)
            scaffold["top_funder"] = top_journal[0][0] if top_journal else "Publication evidence"
            con.execute(
                """
                INSERT INTO gold_scaffold_stats (
                    scaffold, evidence_count, representative_doi, top_funder, total_funding
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(scaffold) DO UPDATE SET
                    evidence_count = excluded.evidence_count,
                    representative_doi = excluded.representative_doi,
                    top_funder = excluded.top_funder,
                    total_funding = excluded.total_funding
                """,
                [
                    scaffold["scaffold"],
                    scaffold["evidence_count"],
                    scaffold["representative_doi"],
                    scaffold["top_funder"],
                    scaffold["total_funding"],
                ],
            )
            x, y, z = _stable_coordinates(scaffold["scaffold"], index, scaffold["evidence_count"])
            con.execute(
                """
                INSERT INTO gold_galaxy_points (
                    id, x, y, z, cluster_id, scaffold, funding_usd
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    x = excluded.x,
                    y = excluded.y,
                    z = excluded.z,
                    cluster_id = excluded.cluster_id,
                    scaffold = excluded.scaffold,
                    funding_usd = excluded.funding_usd
                """,
                [
                    _point_id(scaffold["scaffold"]),
                    x,
                    y,
                    z,
                    _cluster_id(scaffold["category"]),
                    scaffold["scaffold"],
                    scaffold["total_funding"],
                ],
            )
            updated += 1
            points += 1

    report_path = _write_match_report(path, scaffold_terms, publications, matches)
    return ScaffoldMatchResult(
        scaffold_terms=len(scaffold_terms),
        publications_scanned=len(publications),
        matched_scaffolds=len(matches),
        updated_scaffolds=updated,
        galaxy_points=points,
        report_path=str(report_path),
    )

def load_scaffold_terms(path: str | Path) -> list[str]:
    return [entry.name for entry in _load_scaffold_entries(path)]

def _load_scaffold_entries(path: str | Path) -> list[ScaffoldTerm]:
    source = Path(path)
    text = source.read_text(encoding="utf-8-sig", errors="replace")
    terms: list[ScaffoldTerm] = []
    seen: set[str] = set()
    category = "Uncategorized scaffolds"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_category_header(line):
            category = _clean_text(line)
            continue
        line = _clean_text(line)
        key = line.lower()
        if line and key not in seen:
            terms.append(ScaffoldTerm(line, category))
            seen.add(key)
    return terms

def _is_category_header(line: str) -> bool:
    return bool(re.match(r"^\s*\d+\s*(?:[-\u2010-\u2015]|â€“|â€”)?\s*\d*\s*:", line))

def _publication_text(row: tuple[Any, ...]) -> str:
    topics = ""
    try:
        topics = " ".join(json.loads(row[5] or "[]"))
    except (TypeError, json.JSONDecodeError):
        topics = str(row[5] or "")
    return _clean_text(" ".join(str(value or "") for value in (row[1], row[3], row[4], topics))).lower()

def _publication_source(row: tuple[Any, ...]) -> str:
    if row[3]:
        return _clean_text(str(row[3]))
    try:
        raw = json.loads(row[7] or "{}")
    except (TypeError, json.JSONDecodeError, IndexError):
        return ""

    journals = raw.get("journals")
    if isinstance(journals, list) and journals:
        first = journals[0]
        if isinstance(first, str):
            return _clean_text(first)
        if isinstance(first, dict):
            for key in ("title", "name", "sourceTitle"):
                if first.get(key):
                    return _clean_text(str(first[key]))

    for key in ("publisher", "sourceTitle", "sourceName", "dataProvider"):
        if raw.get(key):
            return _clean_text(str(raw[key]))

    providers = raw.get("dataProviders")
    if isinstance(providers, list) and providers:
        first = providers[0]
        if isinstance(first, str):
            return _clean_text(first)
        if isinstance(first, dict) and first.get("name"):
            return _clean_text(str(first["name"]))
    return ""

def _aliases_for_scaffold(scaffold: str) -> list[str]:
    aliases = [scaffold]
    if "/" in scaffold:
        aliases.extend(part.strip() for part in scaffold.split("/") if part.strip())
    lowered = scaffold.lower()
    for suffix in (" core", " motif", " scaffold"):
        if lowered.endswith(suffix):
            aliases.append(scaffold[: -len(suffix)].strip())
    return [_clean_text(alias).lower() for alias in aliases if alias.strip()]

def _alias_pattern(aliases: list[str]) -> re.Pattern[str]:
    escaped = []
    for alias in aliases:
        boundary_left = r"(?<![a-z0-9])"
        boundary_right = r"(?![a-z0-9])"
        escaped.append(boundary_left + re.escape(alias).replace(r"\ ", r"\s+") + boundary_right)
    return re.compile("|".join(escaped), re.IGNORECASE)

def _clean_text(value: str) -> str:
    cleaned = (
        value.replace("â€“", "-")
        .replace("â€”", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("‑", "-")
        .replace("‐", "-")
        .strip()
    )
    return cleaned.strip("'\"")

def _stable_coordinates(scaffold: str, index: int, evidence_count: int) -> tuple[float, float, float]:
    digest = hashlib.sha256(scaffold.encode("utf-8")).digest()
    angle = (int.from_bytes(digest[:2], "big") / 65535) * math.tau
    radius = 0.55 + (index % 11) * 0.045
    height = min(math.log1p(max(evidence_count, 1)) / 5.0, 1.0) * 1.4 - 0.7
    return round(math.cos(angle) * radius, 4), round(height, 4), round(math.sin(angle) * radius, 4)

def _point_id(scaffold: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", scaffold.lower()).strip("_")
    return f"paper_scaffold_{slug}"

def _cluster_id(category: str) -> str:
    match = re.match(r"^(\d+)", category)
    if match:
        return f"paper_scaffold_category_{int(match.group(1)):03d}"
    digest = hashlib.sha1(category.encode("utf-8")).hexdigest()[:8]
    return f"paper_scaffold_category_{digest}"

def _write_match_report(
    scaffold_list_path: Path,
    scaffold_terms: list[ScaffoldTerm],
    publications: list[tuple[Any, ...]],
    matches: dict[str, dict[str, Any]],
) -> Path:
    config = get_config()
    report_dir = Path(config.storage_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_path = report_dir / f"scaffold-publication-match-{timestamp}.md"
    ordered_matches = sorted(matches.values(), key=lambda item: (-item["evidence_count"], item["scaffold"]))
    unmatched_count = len(scaffold_terms) - len(matches)

    lines = [
        "# ChemPulse Scaffold Galaxy Refresh Report",
        "",
        f"- Generated UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Scaffold list: `{scaffold_list_path}`",
        f"- Scaffold terms scanned: `{len(scaffold_terms)}`",
        f"- Publications scanned: `{len(publications)}`",
        f"- Paper-evidenced scaffolds added to galaxy: `{len(matches)}`",
        f"- Scaffold terms with no current paper evidence: `{unmatched_count}`",
        f"- Database: `{config.database_path}`",
        "",
        "## Top Matched Scaffolds",
        "",
    ]
    if not ordered_matches:
        lines.append("No scaffold terms were found in the current publication corpus.")
    else:
        for item in ordered_matches[:50]:
            doi = item["representative_doi"] or "no DOI captured"
            lines.append(f"- {item['scaffold']}: `{item['evidence_count']}` publications, representative DOI/source `{doi}`")
        if len(ordered_matches) > 50:
            lines.append(f"- ...and {len(ordered_matches) - 50} more matched scaffolds.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path

def _initialize_gold_schema_with_retry() -> None:
    get_db_path().parent.mkdir(parents=True, exist_ok=True)
    with _get_connection_with_retry(read_only=False) as con:
        con.execute(GOLD_SCHEMA_SQL)

def _get_connection_with_retry(read_only: bool = False, attempts: int = 60, delay_seconds: float = 2.0) -> duckdb.DuckDBPyConnection:
    last_error: duckdb.Error | OSError | None = None
    for _ in range(attempts):
        try:
            return get_connection(read_only=read_only)
        except (duckdb.Error, OSError) as exc:
            last_error = exc
            if not _is_lock_error(exc):
                raise
            time.sleep(delay_seconds)
    raise RuntimeError(f"Timed out waiting for DuckDB database lock: {last_error}")

def _is_lock_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "lock" in message or "being used by another process" in message or "cannot access the file" in message

def main() -> None:
    parser = argparse.ArgumentParser(description="Add publication-evidenced scaffolds to the ChemPulse galaxy map.")
    parser.add_argument(
        "path",
        nargs="?",
        default=str(default_scaffold_list_path()),
        help="Path to scaffolds.txt. Defaults to ~/Desktop/scaffolds.txt.",
    )
    args = parser.parse_args()
    print(refresh_scaffold_matches(args.path).as_dict())

if __name__ == "__main__":
    main()