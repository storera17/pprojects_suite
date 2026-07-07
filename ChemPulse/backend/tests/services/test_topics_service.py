
from __future__ import annotations

import pytest

from backend.agents.core_publication_agent import CoreApiSettings, CorePublicationAgentSettings
from backend.services import topics_service as svc
from backend.services import chempulse_publication_job as job_mod
from backend.services.chempulse_publication_job import ChemPulsePublicationJob


@pytest.fixture(autouse=True)
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    for var in ("CHEMPULSE_TARGET_COUNT", "CHEMPULSE_CORE_DAILY_LIMIT",
                "CHEMPULSE_CORE_MIN_INSERTED_SUCCESS"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


# --- normalization + validation ---------------------------------------------

def test_normalize_collapses_whitespace():
    assert svc.normalize_term("  cross   coupling \n") == "cross coupling"


def test_validate_rejects_empty_long_and_forbidden():
    assert svc.validate_term("   ") is not None
    assert svc.validate_term("x" * 200) is not None
    assert svc.validate_term('bad "quote"') is not None
    assert svc.validate_term("organocatalysis") is None


def test_set_topics_dedupes_and_reports_errors():
    result = svc.set_topics(["Catalyst", "catalyst", "  ", "cross  coupling", "bad(paren)"])
    terms = [t["term"] for t in result["topics"]]
    assert terms == ["Catalyst", "cross coupling"]   # deduped (case-insensitive) + normalized
    assert result["ok"] is False and len(result["errors"]) == 2   # blank + paren rejected


# --- enable/disable + active terms ------------------------------------------

def test_enable_disable_and_active_terms():
    svc.set_topics(["catalyst", "ligand"])
    svc.set_enabled("ligand", False)
    assert svc.active_terms() == ["catalyst"]
    svc.set_enabled("ligand", True)
    assert set(svc.active_terms()) == {"catalyst", "ligand"}


# --- safe Command Center updates --------------------------------------------

def test_update_from_command_center_replace_and_enable():
    out = svc.update_from_command_center({"topics": ["heterocycle", "esterification"]})
    assert out["ok"] and {t["term"] for t in out["topics"]} == {"heterocycle", "esterification"}
    out2 = svc.update_from_command_center({"enable": {"esterification": False}})
    assert svc.active_terms() == ["heterocycle"]


def test_update_from_command_center_is_safe_on_bad_input():
    assert svc.update_from_command_center("nope")["ok"] is False
    mixed = svc.update_from_command_center({"topics": ["ok-topic", 'bad"q"']})
    assert mixed["ok"] is False and mixed["errors"]
    assert [t["term"] for t in mixed["topics"]] == ["ok-topic"]   # valid one still persisted


def test_compile_query_and_seeding():
    assert svc.list_topics() == []
    seeded = svc.ensure_seeded()
    assert seeded > 0 and svc.list_topics()
    q = svc.compile_query()
    assert q and "yearPublished>={year}" in q


# --- flows into the adapter (normalized → CorePublicationAgent) -------------

class _FakeAgent:
    last: dict = {}

    def __init__(self, client, settings):
        _FakeAgent.last = {"settings": settings}

    def run_once(self):
        return {"status": "succeeded", "inserted": 0, "inserted_items": [],
                "query": _FakeAgent.last["settings"].query}


def test_adapter_uses_service_active_terms(monkeypatch):
    monkeypatch.setattr(job_mod, "settings_from_env", lambda: (
        CoreApiSettings(api_key="t"), CorePublicationAgentSettings()))
    svc.set_topics(["cross  coupling"])   # messy whitespace; should be normalized
    job = ChemPulsePublicationJob(client=object(), agent_factory=_FakeAgent)  # default provider
    job.run()
    query = _FakeAgent.last["settings"].query
    assert '"cross coupling"' in query   # normalized + quoted in the CORE query


# --- optional YAML export/import (skipped if PyYAML absent) ------------------

def test_yaml_export_import_roundtrip(tmp_path):
    pytest.importorskip("yaml")
    svc.set_topics(["catalyst", "ligand"])
    svc.set_enabled("ligand", False)
    path = svc.export_to_yaml(tmp_path / "topics.yaml")
    assert path.exists()
    svc.set_topics(["something-else"])          # clobber DuckDB
    svc.import_from_yaml(path)                   # restore from YAML
    terms = {t["term"]: t["enabled"] for t in svc.list_topics()}
    assert terms == {"catalyst": True, "ligand": False}
