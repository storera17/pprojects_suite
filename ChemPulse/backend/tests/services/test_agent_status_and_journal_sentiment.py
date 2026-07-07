from __future__ import annotations

from backend.agents.core_publication_agent import CorePublicationAgent, CorePublicationAgentSettings
from backend.data.core_publication_repository import CorePublicationRepository, ensure_core_ingestion_schema
from backend.services.agent_status_service import AgentStatusService
from backend.services.journal_sentiment_service import JournalSentimentService
import backend.services.agent_status_service as agent_status_module


class SuccessfulClient:
    def search_works(self, query: str, limit: int, offset: int = 0, entity_type: str = "journal-article", sort: str = "") -> list[dict]:
        if offset:
            return []
        return [
            {
                "id": "success-1",
                "title": "Improved robust catalytic scaffold",
                "doi": "10.1000/success",
                "yearPublished": 2026,
                "authors": [{"name": "Ada Chemist"}],
                "sourceName": "Journal Alpha",
                "abstract": "A stable and efficient reaction.",
                "topics": ["chemistry"],
            }
        ]


class FailingClient:
    def search_works(self, *args, **kwargs) -> list[dict]:
        raise RuntimeError("CORE request failed with CORE_API_KEY=[redacted]")


class InterruptedClient:
    def search_works(self, *args, **kwargs) -> list[dict]:
        raise KeyboardInterrupt()


def test_status_panel_loads_without_api_key(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(agent_status_module, "is_api_key_configured", lambda: False)
    monkeypatch.setattr(agent_status_module, "masked_secret_status", lambda: "Not configured")
    ensure_core_ingestion_schema()

    status = AgentStatusService.get_status()

    assert status["api_key_configured"] is False
    assert status["api_key_display"] == "Not configured"
    assert status["agent_wired_to_app"] is True


def test_status_avoids_database_while_collection_is_running(monkeypatch) -> None:
    monkeypatch.setattr(agent_status_module.ScheduledCollectionService, "is_running", staticmethod(lambda: True))
    monkeypatch.setattr(
        agent_status_module.CorePublicationRepository,
        "agent_run_status",
        staticmethod(lambda: (_ for _ in ()).throw(AssertionError("database should not be touched"))),
    )

    status = AgentStatusService.get_status()

    assert status["collection_running"] is True
    assert status["latest_run_status"] == "running"
    assert "CORE_API_KEY" not in str(status)


def test_api_key_presence_detected_without_secret_exposure(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(agent_status_module, "is_api_key_configured", lambda: True)
    monkeypatch.setattr(agent_status_module, "masked_secret_status", lambda: "[configured]")
    ensure_core_ingestion_schema()

    status = AgentStatusService.get_status()

    assert status["api_key_configured"] is True
    assert status["api_key_display"] == "[configured]"
    assert "SECRET_CORE_KEY" not in str(status)


def test_successful_agent_run_updates_last_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(agent_status_module, "is_api_key_configured", lambda: True)
    monkeypatch.setattr(agent_status_module, "masked_secret_status", lambda: "[configured]")
    agent = CorePublicationAgent(SuccessfulClient(), CorePublicationAgentSettings(query="chemistry", daily_limit=1, page_size=1, min_inserted_success=1))

    agent.run_once()
    status = AgentStatusService.get_status()

    assert status["last_success_time"] != "Never"
    assert status["last_success_records"] == 1
    assert status["latest_run_status"] == "succeeded"
    assert status["latest_run_query"] == "chemistry"
    assert status["latest_run_downloaded_count"] == 1


def test_insufficient_agent_run_exposes_diagnostics(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    agent = CorePublicationAgent(SuccessfulClient(), CorePublicationAgentSettings(query="chemistry", daily_limit=1, page_size=1, min_inserted_success=2))

    agent.run_once()
    status = AgentStatusService.get_status()

    assert status["latest_run_status"] == "insufficient"
    assert status["last_insufficient_time"] != "Never"
    assert status["latest_run_downloaded_count"] == 1
    assert status["latest_run_inserted_count"] == 1
    assert status["latest_run_diagnosis_path"] == "low-yield-query -> insufficient-new-records"
    assert "required at least 2" in status["latest_run_reason"]


def test_failed_agent_run_updates_last_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    agent = CorePublicationAgent(FailingClient(), CorePublicationAgentSettings(query="chemistry", daily_limit=1, page_size=1))

    try:
        agent.run_once()
    except RuntimeError:
        pass
    status = AgentStatusService.get_status()

    assert status["last_failure_time"] != "Never"
    assert status["latest_run_status"] == "failed"
    assert "CORE_API_KEY" not in status["last_failure_error"]


def test_interrupted_agent_run_closes_run_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    agent = CorePublicationAgent(InterruptedClient(), CorePublicationAgentSettings(query="chemistry", daily_limit=1, page_size=1))

    try:
        agent.run_once()
    except KeyboardInterrupt:
        pass
    status = AgentStatusService.get_status()

    assert status["latest_run_status"] == "failed"
    assert status["last_failure_time"] != "Never"
    assert "KeyboardInterrupt" in status["last_failure_error"]


def test_journal_dropdown_receives_available_journals(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_sentiment_publications()

    journals = JournalSentimentService.available_journals()

    assert journals == ["Journal Alpha", "Journal Beta"]


def test_sentiment_graph_data_returned_for_selected_journal(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_sentiment_publications()

    analysis = JournalSentimentService.analyze("Journal Alpha")
    figure = JournalSentimentService.figure("Journal Alpha")

    assert analysis["has_data"] is True
    assert analysis["article_count"] == 2
    assert analysis["average_score"] > 0
    assert len(figure.data) == 1
    assert len(figure.data[0].y) == 2


def test_empty_sentiment_data_returns_safe_empty_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    ensure_core_ingestion_schema()

    analysis = JournalSentimentService.analyze("Missing Journal")
    figure = JournalSentimentService.figure("Missing Journal")

    assert analysis["has_data"] is False
    assert analysis["empty_message"]
    assert len(figure.data) == 0


def _seed_sentiment_publications() -> None:
    CorePublicationRepository.upsert_publications(
        [
            {
                "core_id": "alpha-1",
                "title": "Improved stable scaffold",
                "doi": "10.1000/a1",
                "year_published": 2024,
                "published_date": "2024-01-01",
                "authors": ["Ada"],
                "journal": "Journal Alpha",
                "abstract": "A robust and efficient catalytic system.",
                "topics": ["chemistry"],
                "full_text_url": None,
                "source_url": None,
                "raw": {"id": "alpha-1"},
            },
            {
                "core_id": "alpha-2",
                "title": "Promising selective molecule",
                "doi": "10.1000/a2",
                "year_published": 2025,
                "published_date": "2025-01-01",
                "authors": ["Grace"],
                "journal": "Journal Alpha",
                "abstract": "Enhanced potency with stable handling.",
                "topics": ["chemistry"],
                "full_text_url": None,
                "source_url": None,
                "raw": {"id": "alpha-2"},
            },
            {
                "core_id": "beta-1",
                "title": "Limited unstable scaffold",
                "doi": "10.1000/b1",
                "year_published": 2025,
                "published_date": "2025-01-01",
                "authors": ["Linus"],
                "journal": "Journal Beta",
                "abstract": "Poor selectivity and toxic profile.",
                "topics": ["chemistry"],
                "full_text_url": None,
                "source_url": None,
                "raw": {"id": "beta-1"},
            },
        ],
        "chemistry",
    )
