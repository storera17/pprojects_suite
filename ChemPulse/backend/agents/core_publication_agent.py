from __future__ import annotations

import argparse
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.config import get_config, get_secret_env, is_api_key_configured
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.publication_relevance import DEFAULT_MIN_INGESTION_RELEVANCE_SCORE, is_ingestion_relevant
from backend.data.scaffold_publication_matcher import default_scaffold_list_path, refresh_scaffold_matches
from backend.integrations.core_api import CoreApiClient, CoreApiSettings, normalize_core_work


LEGACY_DEFAULT_QUERY = '((chemistry OR "chemical synthesis" OR catalyst OR scaffold OR molecule) AND yearPublished:{year})'
DEFAULT_EMPTY_RESULT_FALLBACK_QUERY = LEGACY_DEFAULT_QUERY
DEFAULT_QUERY = (
    '((catalyst OR catalysis OR catalytic OR photocatalysis OR electrocatalysis OR organocatalysis '
    'OR "molecular scaffold" OR "chemical scaffold" OR "medicinal chemistry" OR heterocycle '
    'OR ligand OR "cross-coupling" OR "reaction mechanism" OR esterification) '
    'AND (chemistry OR synthesis OR reaction OR molecular OR compound) '
    'AND publishedDate>={since})'
)


@dataclass(frozen=True)
class CorePublicationAgentSettings:
    query: str = DEFAULT_QUERY
    daily_limit: int = 100
    page_size: int = 25
    entity_type: str = "journal-article"
    lookback_days: int = 2
    fallback_lookback_days: int = 90
    fallback_step_days: int = 14
    empty_result_fallback_query: str = DEFAULT_EMPTY_RESULT_FALLBACK_QUERY
    request_interval_seconds: float = 11.0
    base_url: str = "https://api.core.ac.uk/v3"
    sort: str = "recency"
    max_scan_pages: int = 20
    min_relevance_score: int = DEFAULT_MIN_INGESTION_RELEVANCE_SCORE
    min_inserted_success: int = 15
    cursor_overlap_days: int = 7


@dataclass(frozen=True)
class DownloadDiagnostics:
    downloaded_count: int = 0
    duplicate_count: int = 0
    fallback_used: bool = False
    broad_fallback_used: bool = False


class CorePublicationAgent:
    def __init__(self, client: CoreApiClient, settings: CorePublicationAgentSettings) -> None:
        self.client = client
        self.settings = settings

    def run_once(self) -> dict[str, Any]:
        run_id = str(uuid.uuid4())
        initial_since = self._since_date()
        query = self._build_query(initial_since)
        reconciled_runs = CorePublicationRepository.reconcile_orphaned_runs()
        stale_runs = reconciled_runs.get("stale_failed", 0)
        superseded_runs = reconciled_runs.get("superseded_running", 0) + reconciled_runs.get("superseded_legacy_failures", 0)
        CorePublicationRepository.start_run(
            run_id=run_id,
            query=query,
            requested_limit=self.settings.daily_limit,
            page_size=self.settings.page_size,
            initial_query=query,
        )

        inserted = 0
        updated = 0
        downloaded_count = 0
        diagnosis_path = ""
        try:
            publications, final_query, attempted_queries, diagnostics, frontier = self._download_publications_with_fallback(initial_since)
            CorePublicationRepository.update_run_query(run_id, final_query)
            counts = CorePublicationRepository.upsert_publications(publications, final_query)
            scaffold_matches = _refresh_scaffolds_if_available()
            downloaded_count = diagnostics.downloaded_count
            inserted = counts["inserted"]
            updated = counts["updated"]
            error_message, diagnosis_path = _collection_outcome(inserted, self.settings.min_inserted_success, diagnostics)
            status = "insufficient" if error_message else "succeeded"
            CorePublicationRepository.finish_run(
                run_id,
                status,
                inserted,
                updated,
                error_message,
                downloaded_count=downloaded_count,
                diagnosis_path=diagnosis_path,
            )
            if frontier:
                self._advance_cursor(frontier, final_query, downloaded_count, status)
            result = {
                "run_id": run_id,
                "status": status,
                "query": final_query,
                "initial_query": query,
                "attempted_queries": attempted_queries,
                "downloaded": downloaded_count,
                "inserted": inserted,
                "updated": updated,
                "diagnosis_path": diagnosis_path,
                "inserted_items": counts.get("inserted_items", []),
                "updated_items": counts.get("updated_items", []),
                "stale_runs_marked_failed": stale_runs,
                "orphaned_runs_superseded": superseded_runs,
                "scaffold_matches": scaffold_matches,
            }
            if error_message:
                result["error"] = error_message
            result["report_path"] = str(write_run_report(result))
            return result
        except Exception as exc:
            CorePublicationRepository.finish_run(run_id, "failed", inserted, updated, str(exc), downloaded_count=downloaded_count, diagnosis_path=diagnosis_path)
            failure_result = {
                "run_id": run_id,
                "status": "failed",
                "query": query,
                "downloaded": downloaded_count,
                "inserted": inserted,
                "updated": updated,
                "diagnosis_path": diagnosis_path,
                "inserted_items": [],
                "updated_items": [],
                "error": str(exc),
                "stale_runs_marked_failed": stale_runs,
                "orphaned_runs_superseded": superseded_runs,
                "scaffold_matches": {},
            }
            failure_result["report_path"] = str(write_run_report(failure_result))
            raise
        except BaseException as exc:
            interrupted_error = f"Run was interrupted before completion: {type(exc).__name__}"
            CorePublicationRepository.finish_run(
                run_id,
                "failed",
                inserted,
                updated,
                interrupted_error,
                downloaded_count=downloaded_count,
                diagnosis_path=diagnosis_path,
            )
            failure_result = {
                "run_id": run_id,
                "status": "failed",
                "query": query,
                "downloaded": downloaded_count,
                "inserted": inserted,
                "updated": updated,
                "diagnosis_path": diagnosis_path,
                "inserted_items": [],
                "updated_items": [],
                "error": interrupted_error,
                "stale_runs_marked_failed": stale_runs,
                "orphaned_runs_superseded": superseded_runs,
                "scaffold_matches": {},
            }
            failure_result["report_path"] = str(write_run_report(failure_result))
            raise

    def _download_publications_with_fallback(
        self, initial_since: datetime
    ) -> tuple[list[dict[str, Any]], str, list[str], DownloadDiagnostics, dict[str, str] | None]:
        attempted_queries: list[str] = []
        final_query = self._build_query(initial_since)
        last_diagnostics = DownloadDiagnostics()
        observed_frontier: dict[str, str] | None = None
        stop_cursor = CorePublicationRepository.ingestion_cursor()

        for since in self._fallback_since_dates(initial_since):
            query = self._build_query(since)
            attempted_queries.append(query)
            final_query = query
            publications, stats = self._download_publications(query, stop_cursor=stop_cursor)
            if observed_frontier is None and stats.get("frontier"):
                observed_frontier = stats["frontier"]
            last_diagnostics = DownloadDiagnostics(
                downloaded_count=stats["downloaded_count"],
                duplicate_count=stats["duplicate_count"],
                fallback_used=len(attempted_queries) > 1,
                broad_fallback_used=False,
            )
            if publications:
                return publications, final_query, attempted_queries, last_diagnostics, observed_frontier
            if stats.get("cursor_reached"):
                return [], final_query, attempted_queries, last_diagnostics, observed_frontier
            if "{since}" not in self.settings.query:
                break

        fallback_query = self._empty_result_fallback_query()
        if fallback_query and fallback_query not in attempted_queries:
            attempted_queries.append(fallback_query)
            final_query = fallback_query
            publications, stats = self._download_publications(fallback_query, stop_cursor=stop_cursor)
            if observed_frontier is None and stats.get("frontier"):
                observed_frontier = stats["frontier"]
            last_diagnostics = DownloadDiagnostics(
                downloaded_count=stats["downloaded_count"],
                duplicate_count=stats["duplicate_count"],
                fallback_used=True,
                broad_fallback_used=True,
            )
            if publications:
                return publications, final_query, attempted_queries, last_diagnostics, observed_frontier
            if stats.get("cursor_reached"):
                return [], final_query, attempted_queries, last_diagnostics, observed_frontier

        return [], final_query, attempted_queries, last_diagnostics, observed_frontier

    def _download_publications(
        self,
        query: str,
        *,
        stop_cursor: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        downloaded: list[dict[str, Any]] = []
        offset = 0
        page_size = min(max(self.settings.page_size, 1), 100)

        scanned_pages = 0
        seen_ids: set[str] = set()
        duplicate_count = 0
        frontier: dict[str, str] | None = None
        cursor_reached = False
        while len(downloaded) < self.settings.daily_limit and scanned_pages < self.settings.max_scan_pages:
            remaining = self.settings.daily_limit - len(downloaded)
            limit = min(page_size, remaining)
            results = self.client.search_works(
                query=query,
                limit=limit,
                offset=offset,
                entity_type=self.settings.entity_type,
                sort=self.settings.sort,
            )
            if not results:
                break

            page_publications: list[dict[str, Any]] = []
            for work in results:
                if frontier is None:
                    frontier = _cursor_from_work(work)
                current_cursor = _cursor_from_work(work)
                if stop_cursor and current_cursor and _cursor_reached(current_cursor, stop_cursor):
                    cursor_reached = True
                    break
                normalized = normalize_core_work(work)
                if normalized and is_ingestion_relevant(normalized, self.settings.min_relevance_score):
                    page_publications.append(normalized)

            existing_ids = CorePublicationRepository.existing_core_ids(
                [str(publication["core_id"]) for publication in page_publications]
            )
            for publication in page_publications:
                core_id = str(publication["core_id"])
                if core_id in seen_ids or core_id in existing_ids:
                    duplicate_count += 1
                    continue
                downloaded.append(publication)
                seen_ids.add(core_id)
                if len(downloaded) >= self.settings.daily_limit:
                    break

            if cursor_reached or len(results) < limit:
                break
            offset += limit
            scanned_pages += 1

        return downloaded, {
            "downloaded_count": len(downloaded),
            "duplicate_count": duplicate_count,
            "frontier": frontier,
            "cursor_reached": cursor_reached,
        }

    def _build_query(self, since: datetime) -> str:
        return self.settings.query.format(since=since.date().isoformat(), year=datetime.now(timezone.utc).year)

    def _empty_result_fallback_query(self) -> str:
        query = self.settings.empty_result_fallback_query.strip()
        return _format_query(query) if query else ""

    def _since_date(self) -> datetime:
        now = datetime.now(timezone.utc)
        cursor = CorePublicationRepository.ingestion_cursor()
        cursor_published_at = _parse_cursor_datetime((cursor or {}).get("frontier_published_date", ""))
        if cursor_published_at is not None:
            overlap_days = max(self.settings.cursor_overlap_days, 0)
            return min(cursor_published_at - timedelta(days=overlap_days), now)
        latest_success = CorePublicationRepository.latest_successful_run_started_at()
        if latest_success is None:
            return now - timedelta(days=self.settings.lookback_days)
        return min(latest_success + timedelta(days=1), now)

    def _advance_cursor(self, frontier: dict[str, str], query: str, downloaded_count: int, status: str) -> None:
        existing = CorePublicationRepository.ingestion_cursor()
        if existing and not _cursor_is_newer(frontier, existing):
            return
        CorePublicationRepository.upsert_ingestion_cursor(
            "core",
            frontier_core_id=frontier.get("frontier_core_id", ""),
            frontier_published_date=frontier.get("frontier_published_date", ""),
            query=query,
            metadata={
                "status": status,
                "downloaded_count": int(downloaded_count),
            },
        )

    def _fallback_since_dates(self, initial_since: datetime) -> list[datetime]:
        dates = [initial_since]
        if "{since}" not in self.settings.query:
            return dates

        fallback_lookback_days = max(self.settings.fallback_lookback_days, 0)
        fallback_step_days = max(self.settings.fallback_step_days, 1)
        for days_back in range(fallback_step_days, fallback_lookback_days + 1, fallback_step_days):
            dates.append(initial_since - timedelta(days=days_back))
        if fallback_lookback_days and (fallback_lookback_days % fallback_step_days):
            dates.append(initial_since - timedelta(days=fallback_lookback_days))
        return dates


def settings_from_env() -> tuple[CoreApiSettings, CorePublicationAgentSettings]:
    if not is_api_key_configured():
        raise RuntimeError("CORE_API_KEY is not set. Store your CORE key in the user environment before running the agent.")
    api_key = get_config().literature_api_key.strip()

    agent_settings = CorePublicationAgentSettings(
        query=_core_query_from_env(),
        daily_limit=_env_int("CHEMPULSE_CORE_DAILY_LIMIT", 100),
        page_size=_env_int("CHEMPULSE_CORE_PAGE_SIZE", 25),
        entity_type=get_secret_env("CHEMPULSE_CORE_ENTITY_TYPE", "journal-article"),
        lookback_days=_env_int("CHEMPULSE_CORE_LOOKBACK_DAYS", 2),
        fallback_lookback_days=_env_int("CHEMPULSE_CORE_FALLBACK_LOOKBACK_DAYS", 90),
        fallback_step_days=_env_int("CHEMPULSE_CORE_FALLBACK_STEP_DAYS", 14),
        empty_result_fallback_query=get_secret_env("CHEMPULSE_CORE_EMPTY_RESULT_FALLBACK_QUERY", DEFAULT_EMPTY_RESULT_FALLBACK_QUERY),
        request_interval_seconds=_env_float("CHEMPULSE_CORE_REQUEST_INTERVAL_SECONDS", 11.0),
        base_url=get_secret_env("CHEMPULSE_CORE_BASE_URL", "https://api.core.ac.uk/v3"),
        sort=get_secret_env("CHEMPULSE_CORE_SORT", "recency"),
        max_scan_pages=_env_int("CHEMPULSE_CORE_MAX_SCAN_PAGES", 20),
        min_relevance_score=_env_int("CHEMPULSE_CORE_MIN_RELEVANCE_SCORE", DEFAULT_MIN_INGESTION_RELEVANCE_SCORE),
        min_inserted_success=_env_int("CHEMPULSE_CORE_MIN_INSERTED_SUCCESS", 15),
        cursor_overlap_days=_env_int("CHEMPULSE_CORE_CURSOR_OVERLAP_DAYS", 7),
    )
    api_settings = CoreApiSettings(
        api_key=api_key,
        base_url=agent_settings.base_url,
        request_interval_seconds=agent_settings.request_interval_seconds,
    )
    return api_settings, agent_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download filtered CORE journal publication metadata into ChemPulse.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved settings without calling CORE.")
    args = parser.parse_args(argv)

    try:
        api_settings, agent_settings = settings_from_env()
    except RuntimeError as exc:
        run_id = str(uuid.uuid4())
        query = DEFAULT_QUERY.format(since=datetime.now(timezone.utc).date().isoformat(), year=datetime.now(timezone.utc).year)
        CorePublicationRepository.start_run(run_id=run_id, query=query, requested_limit=0, page_size=0)
        CorePublicationRepository.finish_run(run_id, "failed", 0, 0, str(exc))
        write_run_report(
            {
                "run_id": run_id,
                "status": "failed",
                "query": query,
                "downloaded": 0,
                "inserted": 0,
                "updated": 0,
                "inserted_items": [],
                "updated_items": [],
                "error": str(exc),
                "stale_runs_marked_failed": 0,
                "orphaned_runs_superseded": 0,
                "scaffold_matches": {},
            }
        )
        print(str(exc))
        return 1
    if args.dry_run:
        print(
            {
                "base_url": api_settings.base_url,
                "query": agent_settings.query,
                "daily_limit": agent_settings.daily_limit,
                "page_size": agent_settings.page_size,
                "entity_type": agent_settings.entity_type,
                "request_interval_seconds": agent_settings.request_interval_seconds,
                "sort": agent_settings.sort,
                "max_scan_pages": agent_settings.max_scan_pages,
                "min_relevance_score": agent_settings.min_relevance_score,
                "min_inserted_success": agent_settings.min_inserted_success,
                "fallback_lookback_days": agent_settings.fallback_lookback_days,
                "fallback_step_days": agent_settings.fallback_step_days,
                "empty_result_fallback_query": agent_settings.empty_result_fallback_query,
            }
        )
        return 0

    result = CorePublicationAgent(CoreApiClient(api_settings), agent_settings).run_once()
    print(result)
    return 0 if result.get("status") == "succeeded" else 1


def write_run_report(result: dict[str, Any]) -> Path:
    config = get_config()
    report_dir = Path(get_secret_env("CHEMPULSE_REPORT_DIR", str(config.storage_dir / "reports")))
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report_path = report_dir / f"core-publication-agent-{timestamp}-{result['run_id']}.md"
    database_path = config.database_path

    lines = [
        "# ChemPulse Scheduled CORE Ingestion Report",
        "",
        f"- Run ID: `{result['run_id']}`",
        f"- Status: `{result['status']}`",
        f"- Generated UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Query: `{result.get('query', '')}`",
        f"- Initial query: `{result.get('initial_query', result.get('query', ''))}`",
        f"- Query attempts: `{len(result.get('attempted_queries', [])) or 1}`",
        f"- Downloaded records: `{result.get('downloaded', 0)}`",
        f"- Inserted records: `{result.get('inserted', 0)}`",
        f"- Updated records: `{result.get('updated', 0)}`",
        f"- Diagnosis path: `{result.get('diagnosis_path', '') or 'n/a'}`",
        f"- Stale running runs marked failed: `{result.get('stale_runs_marked_failed', 0)}`",
        f"- Orphaned runs superseded by later success: `{result.get('orphaned_runs_superseded', 0)}`",
        f"- Publication-evidenced scaffolds refreshed: `{result.get('scaffold_matches', {}).get('matched_scaffolds', 0)}`",
        "",
        "## Runtime Files Updated",
        "",
        f"- Database: `{database_path}`",
        f"- Report: `{report_path}`",
        "",
        "## New Publications",
        "",
        *_format_items(result.get("inserted_items", [])),
        "",
        "## Updated Publications",
        "",
        *_format_items(result.get("updated_items", [])),
    ]
    if result.get("error"):
        lines.extend(["", "## Error", "", f"```text\n{result['error']}\n```"])
    attempted_queries = result.get("attempted_queries", [])
    if attempted_queries:
        lines.extend(["", "## Query Attempts", ""])
        lines.extend([f"- `{query}`" for query in attempted_queries])

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _format_items(items: list[dict[str, str]], limit: int = 25) -> list[str]:
    if not items:
        return ["No records in this category."]

    formatted = []
    for item in items[:limit]:
        title = item.get("title", "Untitled")
        core_id = item.get("core_id", "")
        year = item.get("year", "n/a")
        journal = item.get("journal", "Unknown source")
        doi = item.get("doi", "")
        doi_suffix = f" DOI: `{doi}`" if doi else ""
        formatted.append(f"- `{core_id}` {title} ({year}, {journal}).{doi_suffix}")
    if len(items) > limit:
        formatted.append(f"- ...and {len(items) - limit} more records.")
    return formatted


def _env_int(name: str, default: int) -> int:
    value = get_secret_env(name)
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = get_secret_env(name)
    return float(value) if value else default


def _core_query_from_env() -> str:
    process_query = os.getenv("CHEMPULSE_CORE_QUERY", "")
    if process_query:
        return _normalize_core_query(process_query)
    query = get_secret_env("CHEMPULSE_CORE_QUERY", DEFAULT_QUERY)
    return _normalize_core_query(query)


def _normalize_core_query(query: str) -> str:
    return DEFAULT_QUERY if query.strip() == LEGACY_DEFAULT_QUERY else query


def _format_query(query: str) -> str:
    return query.format(since=datetime.now(timezone.utc).date().isoformat(), year=datetime.now(timezone.utc).year)


def _cursor_from_work(work: dict[str, Any]) -> dict[str, str] | None:
    core_id = str(work.get("core_id") or work.get("id") or work.get("coreId") or "").strip()
    if not core_id:
        return None
    published_date = str(
        work.get("published_date")
        or work.get("publishedDate")
        or work.get("createdDate")
        or work.get("year_published")
        or work.get("yearPublished")
        or ""
    ).strip()
    return {
        "frontier_core_id": core_id,
        "frontier_published_date": published_date,
    }


def _cursor_reached(current: dict[str, str], stop_cursor: dict[str, Any]) -> bool:
    current_id = str(current.get("frontier_core_id") or "")
    stop_id = str(stop_cursor.get("frontier_core_id") or "")
    if current_id and stop_id and current_id == stop_id:
        return True
    current_published_at = _parse_cursor_datetime(current.get("frontier_published_date", ""))
    stop_published_at = _parse_cursor_datetime(str(stop_cursor.get("frontier_published_date") or ""))
    if current_published_at is None or stop_published_at is None:
        return False
    return current_published_at < stop_published_at


def _cursor_is_newer(candidate: dict[str, str], existing: dict[str, Any]) -> bool:
    candidate_published_at = _parse_cursor_datetime(candidate.get("frontier_published_date", ""))
    existing_published_at = _parse_cursor_datetime(str(existing.get("frontier_published_date") or ""))
    if candidate_published_at and existing_published_at:
        if candidate_published_at > existing_published_at:
            return True
        if candidate_published_at < existing_published_at:
            return False
    candidate_id = str(candidate.get("frontier_core_id") or "")
    existing_id = str(existing.get("frontier_core_id") or "")
    return bool(candidate_id and candidate_id != existing_id)


def _parse_cursor_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    if text.isdigit() and len(text) == 4:
        year = int(text)
        if 1800 <= year <= datetime.now(timezone.utc).year + 1:
            return datetime(year, 1, 1, tzinfo=timezone.utc)
    return None


def _collection_outcome(inserted: int, minimum: int, diagnostics: DownloadDiagnostics) -> tuple[str, str]:
    if minimum <= 0 or inserted >= minimum:
        return "", ""
    diagnosis_path = _diagnosis_path(diagnostics)
    return (
        f"Insufficient CORE collection: inserted {inserted} records; required at least {minimum}. "
        f"Diagnosis path: {diagnosis_path}.",
        diagnosis_path,
    )


def _diagnosis_path(diagnostics: DownloadDiagnostics) -> str:
    if diagnostics.duplicate_count > diagnostics.downloaded_count:
        return "duplicate-heavy-results -> insufficient-new-records"
    if diagnostics.broad_fallback_used:
        return "broad-query-fallback -> insufficient-new-records"
    if diagnostics.fallback_used:
        return "widened-lookback -> insufficient-new-records"
    return "low-yield-query -> insufficient-new-records"


def _refresh_scaffolds_if_available() -> dict[str, int]:
    path = Path(get_secret_env("CHEMPULSE_SCAFFOLD_LIST_PATH", str(default_scaffold_list_path())))
    if not path.exists():
        return {}
    return refresh_scaffold_matches(path).as_dict()


if __name__ == "__main__":
    raise SystemExit(main())
