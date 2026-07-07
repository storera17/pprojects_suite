from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.agents.core_publication_agent import CorePublicationAgent, settings_from_env
from backend.data import topics_repository
from backend.services import topics_service
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.db import query_records
from backend.integrations.core_api import CoreApiClient
from backend.core.paths import storage_dir

DEFAULT_TARGET_COUNT = 25

# Callable seam so tests inject a fake PDF fetcher (no network in tests).
PdfFetcher = Callable[[str, Path], Path | None]
AgentFactory = Callable[[Any, Any], CorePublicationAgent]

class ChemPulsePublicationJob:
    def __init__(
        self,
        *,
        target_count: int = DEFAULT_TARGET_COUNT,
        topics_provider: Callable[[], list[str]] | None = None,
        client: Any | None = None,
        api_settings: Any | None = None,
        agent_settings: Any | None = None,
        agent_factory: AgentFactory | None = None,
        pdf_fetcher: PdfFetcher | None = None,
        storage_root: Path | None = None,
    ) -> None:
        self.target_count = target_count
        self.topics_provider = topics_provider or topics_service.active_terms
        self.client = client
        self.api_settings = api_settings
        self.agent_settings = agent_settings
        self.agent_factory = agent_factory or (lambda c, s: CorePublicationAgent(c, s))
        self.pdf_fetcher = pdf_fetcher or _download_oa_pdf
        self.storage_root = storage_root

    def run(self) -> dict[str, Any]:
        # Normalize topics before anything touches CorePublicationAgent.
        topics = topics_service.normalize_terms(self.topics_provider())
        # Settings can be injected (e.g. by the scheduler, which owns settings_from_env so
        # its error handling/monkeypatch seam stays intact); otherwise resolve them here.
        if self.api_settings is not None and self.agent_settings is not None:
            api_settings, agent_settings = self.api_settings, self.agent_settings
        else:
            api_settings, agent_settings = settings_from_env()

        # Adapter-owned: topics → CORE query (None ⇒ keep the agent's configured default).
        compiled = topics_repository.compile_core_query(topics)
        if compiled is not None:
            agent_settings = replace(agent_settings, query=compiled)
        # Adapter-owned: the M7 collection target (25 unique/run by default). This is the
        # ChemPulse OS knob (CHEMPULSE_TARGET_COUNT), authoritative over the legacy
        # CORE_* limit vars. Dedup/backward-search remain the agent's job; we set the
        # target (download cap + success threshold), the agent collects to it.
        target = _resolve_target(self.target_count)
        agent_settings = replace(
            agent_settings, daily_limit=target, min_inserted_success=target)

        client = self.client or CoreApiClient(api_settings)
        agent = self.agent_factory(client, agent_settings)
        result = agent.run_once()  # ← DELEGATE everything hard to the existing agent

        result["topics"] = topics
        result["target_count"] = self.target_count

        inserted_items = result.get("inserted_items", []) or []
        folder = self._make_dated_folder(len(inserted_items))
        result["folder"] = str(folder)
        self._enrich_stored_records(inserted_items, topics, folder)
        self._write_collection_metadata(folder, result, inserted_items)
        return result

    # --- adapter-owned post-processing --------------------------------------

    def _make_dated_folder(self, count: int) -> Path:
        root = self.storage_root or storage_dir()
        folder = root / "publications" / f"{date.today().isoformat()}-{count}-Files-Collected"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _enrich_stored_records(self, inserted_items: list[dict], topics: list[str],
                               folder: Path) -> None:
        core_ids = [str(i.get("core_id")) for i in inserted_items if i.get("core_id")]
        if not core_ids:
            return
        rows = self._fetch_rows(core_ids)
        for core_id, row in rows.items():
            matched = _match_topic(row, topics)
            file_path = ""
            url = row.get("full_text_url")
            if url:
                saved = self.pdf_fetcher(url, folder / f"{core_id}.pdf")
                if saved is not None:
                    file_path = str(saved)
            CorePublicationRepository.annotate_publication(
                core_id,
                duplicate_status="new",  # duplicates are dropped pre-insert, never stored
                matched_topic=matched,
                file_path=file_path,
                run_folder=str(folder),
            )

    @staticmethod
    def _fetch_rows(core_ids: list[str]) -> dict[str, dict]:
        placeholders = ", ".join(["?"] * len(core_ids))
        records = query_records(
            f"SELECT core_id, title, doi, journal, source_url, full_text_url, topics_json, abstract "
            f"FROM bronze_core_publications WHERE core_id IN ({placeholders})",
            core_ids,
        )
        return {str(r["core_id"]): r for r in records}

    @staticmethod
    def _write_collection_metadata(folder: Path, result: dict, inserted_items: list[dict]) -> None:
        """Write a visible, fabrication-free manifest of the run into the dated folder."""
        payload = {
            "run_id": result.get("run_id"),
            "status": result.get("status"),
            "collected_at": datetime.now(tz=timezone.utc).isoformat(),
            "unique_collected": len(inserted_items),
            "target_count": result.get("target_count"),
            "topics": result.get("topics", []),
            "query": result.get("query"),
            "publications": [
                {k: item.get(k) for k in ("core_id", "title", "doi", "year", "journal")}
                for item in inserted_items
            ],
        }
        (folder / "collection_metadata.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _resolve_target(default: int) -> int:
    """The collection target: CHEMPULSE_TARGET_COUNT env override, else the default (25)."""
    raw = os.getenv("CHEMPULSE_TARGET_COUNT")
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return default


def _match_topic(row: dict, topics: list[str]) -> str | None:
    """The configured topic that actually appears in this publication (substring match over
    title/abstract/topics). Returns None if none match — never fabricates a topic."""
    haystack = " ".join(str(row.get(k) or "") for k in ("title", "abstract", "topics_json")).lower()
    for term in topics:
        if term and term.lower() in haystack:
            return term
    return None


def _download_oa_pdf(url: str, dest: Path) -> Path | None:
    """Download an open-access PDF only. Returns the saved path, or None if the resource
    isn't an openly downloadable PDF. No paywalled/scraped sources."""
    try:
        import requests

        resp = requests.get(url, timeout=30, stream=True)
        if not resp.ok:
            return None
        content_type = resp.headers.get("Content-Type", "").lower()
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            return None  # not an openly-downloadable PDF → store metadata only
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                fh.write(chunk)
        return dest
    except Exception:  # noqa: BLE001 — never let a download failure break collection
        return None
