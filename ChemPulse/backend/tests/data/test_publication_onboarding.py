from __future__ import annotations

import json

import pytest

from backend.agents.core_publication_agent import CoreApiSettings, CorePublicationAgentSettings
from backend.data import topics_repository as topics
from backend.data.core_publication_repository import CorePublicationRepository
from backend.services import chempulse_publication_job as job_mod
from backend.services.chempulse_publication_job import ChemPulsePublicationJob


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    """Point ChemPulse storage (DuckDB + folders) at a temp dir + clean env baseline."""
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    # Isolate from any machine-level ChemPulse config so the default target (25) applies.
    for var in ("CHEMPULSE_TARGET_COUNT", "CHEMPULSE_CORE_DAILY_LIMIT",
                "CHEMPULSE_CORE_MIN_INSERTED_SUCCESS"):
        monkeypatch.delenv(var, raising=False)
    # Adapter must not depend on a real CORE key / env; feed canned settings.
    monkeypatch.setattr(job_mod, "settings_from_env", lambda: (
        CoreApiSettings(api_key="test"), CorePublicationAgentSettings()))
    return tmp_path


# --- Phase B: topics registry + compiler ------------------------------------

def test_topics_roundtrip_and_active():
    topics.set_topics(["Catalyst", "cross-coupling", "catalyst", " "])  # dup + blank dropped
    assert topics.active_topics() == ["Catalyst", "cross-coupling"]
    topics.set_enabled("cross-coupling", False)
    assert topics.active_topics() == ["Catalyst"]


def test_compile_core_query():
    q = topics.compile_core_query(["catalyst", "cross-coupling"])
    assert '"cross-coupling"' in q          # multi-word/hyphen terms quoted
    assert "catalyst" in q
    assert "yearPublished>={year}" in q       # CORE-accepted date filter ({year} templated by agent)
    assert topics.compile_core_query([]) is None
    assert topics.compile_core_query(["  "]) is None


# --- Phase C: adapter delegates to CorePublicationAgent ---------------------

class _FakeAgent:
    """Records that the adapter delegated to the agent; performs no real collection."""
    last = {}

    def __init__(self, client, settings):
        _FakeAgent.last = {"settings": settings, "calls": 0}

    def run_once(self):
        _FakeAgent.last["calls"] += 1
        return {"status": "succeeded", "inserted": 0, "inserted_items": [],
                "query": self_settings_query()}


def self_settings_query():
    return _FakeAgent.last["settings"].query


def test_adapter_delegates_and_passes_target_and_topics():
    job = ChemPulsePublicationJob(
        target_count=25,
        topics_provider=lambda: ["catalyst", "cross-coupling"],
        client=object(),
        agent_factory=_FakeAgent,
    )
    result = job.run()
    s = _FakeAgent.last["settings"]
    assert _FakeAgent.last["calls"] == 1                 # delegated exactly once
    assert s.daily_limit == 25 and s.min_inserted_success == 25   # 25-unique target passed
    assert "catalyst" in s.query and "yearPublished>={year}" in s.query  # topics compiled in
    assert result["topics"] == ["catalyst", "cross-coupling"]


def test_adapter_does_not_dedup_itself(monkeypatch):
    """Dedup is the agent's job; the adapter must never call existing_core_ids."""
    called = {"n": 0}
    monkeypatch.setattr(CorePublicationRepository, "existing_core_ids",
                        staticmethod(lambda ids: called.__setitem__("n", called["n"] + 1) or set()))
    ChemPulsePublicationJob(topics_provider=lambda: [], client=object(),
                            agent_factory=_FakeAgent).run()
    assert called["n"] == 0


def test_empty_topics_keeps_agent_default_query():
    job = ChemPulsePublicationJob(topics_provider=lambda: [], client=object(),
                                  agent_factory=_FakeAgent)
    job.run()
    # query unchanged from the canned default (not overridden to an empty filter)
    assert _FakeAgent.last["settings"].query == CorePublicationAgentSettings().query


# --- Phase C+E: dated folder, DB enrichment, OA PDF policy -------------------

def _pub(core_id, title, *, url=None):
    return {"core_id": core_id, "title": title, "doi": f"10.0/{core_id}",
            "year_published": 2026, "published_date": "2026-06-01", "authors": ["A. Author"],
            "journal": "J. Test", "abstract": "catalyst study", "topics": ["catalysis"],
            "full_text_url": url, "source_url": "https://example.org", "raw": {"id": core_id}}


def _agent_that_inserts(pubs):
    class _Agent:
        def __init__(self, client, settings): pass
        def run_once(self):
            counts = CorePublicationRepository.upsert_publications(pubs, "q")
            return {"status": "succeeded", "inserted": counts["inserted"],
                    "inserted_items": counts["inserted_items"], "query": "q"}
    return _Agent


def test_folder_naming_db_fields_and_oa_pdf(temp_storage, monkeypatch):
    pubs = [_pub("c1", "Catalyst paper", url="https://example.org/c1.pdf"),  # OA → downloaded
            _pub("c2", "Ligand paper", url=None)]                            # no URL → metadata only
    fetched = []
    def fake_fetcher(url, dest):
        fetched.append(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"%PDF-1.4 fake")
        return dest

    job = ChemPulsePublicationJob(
        topics_provider=lambda: ["catalyst"], client=object(),
        agent_factory=_agent_that_inserts(pubs), pdf_fetcher=fake_fetcher)
    result = job.run()

    # dated folder named with X = unique collected
    folder = temp_storage / "publications" / f"{__import__('datetime').date.today().isoformat()}-2-Files-Collected"
    assert folder.is_dir()
    meta = json.loads((folder / "collection_metadata.json").read_text())
    assert meta["unique_collected"] == 2 and len(meta["publications"]) == 2

    # DB enrichment: visible fields populated, no fabrication
    rows = {r["core_id"]: r for r in __import__("backend.data.db", fromlist=["query_records"]).query_records(
        "SELECT core_id, duplicate_status, matched_topic, file_path, run_folder FROM bronze_core_publications")}
    assert rows["c1"]["duplicate_status"] == "new"
    assert rows["c1"]["matched_topic"] == "catalyst"      # derived (abstract contains 'catalyst')
    assert rows["c1"]["file_path"]                         # OA PDF saved
    assert rows["c2"]["file_path"] in ("", None)           # no URL → empty, not fabricated
    assert fetched == ["https://example.org/c1.pdf"]       # only the OA one fetched


def test_oa_pdf_skipped_for_non_pdf(temp_storage):
    # The real fetcher returns None for non-PDF content → file_path stays empty.
    from backend.services.chempulse_publication_job import _download_oa_pdf
    # No network: a clearly-not-a-pdf URL with no server → guarded to None.
    assert _download_oa_pdf("https://example.org/landing-page", temp_storage / "x.pdf") is None