from __future__ import annotations

from datetime import datetime, timezone

from backend.agents.core_publication_agent import DEFAULT_QUERY, CorePublicationAgent, CorePublicationAgentSettings, settings_from_env
from backend.data.db import get_connection
from backend.data.core_publication_repository import CorePublicationRepository, ensure_core_ingestion_schema
from backend.data.publication_relevance import is_ingestion_relevant, publication_relevance
from backend.integrations.core_api import normalize_core_work
import backend.agents.core_publication_agent as core_agent_module


class FakeCoreClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def search_works(
        self,
        query: str,
        limit: int,
        offset: int = 0,
        entity_type: str = "journal-article",
        sort: str = "",
    ) -> list[dict]:
        self.calls.append({"query": query, "limit": limit, "offset": offset, "entity_type": entity_type, "sort": sort})
        if offset > 0:
            return []
        return [
            {
                "id": "core-1",
                "title": "Catalyst discovery",
                "doi": "10.1000/example",
                "yearPublished": 2026,
                "authors": [{"name": "Ada Chemist"}],
                "sourceName": "Journal of Useful Chemistry",
                "abstract": "A useful abstract.",
                "topics": ["chemistry"],
            }
        ]


def test_normalize_core_work_maps_common_fields() -> None:
    normalized = normalize_core_work(
        {
            "id": 123,
            "title": "Molecular scaffold mining",
            "yearPublished": "2025",
            "authors": [{"name": "Grace Hopper"}, "Alan Turing"],
            "sourceTitle": "Chemistry Letters",
            "sourceFulltextUrls": ["https://example.test/fulltext"],
        }
    )

    assert normalized is not None
    assert normalized["core_id"] == "123"
    assert normalized["year_published"] == 2025
    assert normalized["authors"] == ["Grace Hopper", "Alan Turing"]
    assert normalized["journal"] == "Chemistry Letters"
    assert normalized["source_url"] == "https://example.test/fulltext"


def test_core_publication_repository_upserts_records(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    ensure_core_ingestion_schema()

    publication = {
        "core_id": "core-1",
        "title": "Catalyst discovery",
        "doi": "10.1000/example",
        "year_published": 2026,
        "published_date": "2026-05-17",
        "authors": ["Ada Chemist"],
        "journal": "Journal of Useful Chemistry",
        "abstract": "A useful abstract.",
        "topics": ["chemistry"],
        "full_text_url": None,
        "source_url": None,
        "raw": {"id": "core-1"},
    }

    first = CorePublicationRepository.upsert_publications([publication], "chemistry")
    second = CorePublicationRepository.upsert_publications([{**publication, "title": "Updated title"}], "chemistry")
    metrics = CorePublicationRepository.publication_metrics()
    recent = CorePublicationRepository.recent_publications(query="updated")
    journals = CorePublicationRepository.top_journals()

    assert first["inserted"] == 1
    assert first["updated"] == 0
    assert first["inserted_items"][0]["title"] == "Catalyst discovery"
    assert second["inserted"] == 0
    assert second["updated"] == 1
    assert second["updated_items"][0]["title"] == "Updated title"
    assert metrics["publication_count"] == 1
    assert recent[0]["title"] == "Updated title"
    assert journals == [{"label": "Journal of Useful Chemistry", "count": 1}]


def test_core_publication_agent_downloads_and_records_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = FakeCoreClient()
    agent = CorePublicationAgent(
        client,
        CorePublicationAgentSettings(query="chemistry", daily_limit=5, page_size=2, min_inserted_success=1),
    )

    result = agent.run_once()

    assert result["status"] == "succeeded"
    assert result["inserted"] == 1
    assert result["report_path"].endswith(".md")
    assert set(result).isdisjoint({"mail_report", "notification_report"})
    assert client.calls == [{"query": "chemistry", "limit": 2, "offset": 0, "entity_type": "journal-article", "sort": "recency"}]


def test_core_publication_agent_marks_insufficient_insertions_insufficient(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = FakeCoreClient()
    agent = CorePublicationAgent(
        client,
        CorePublicationAgentSettings(query="chemistry", daily_limit=5, page_size=2, min_inserted_success=2),
    )

    result = agent.run_once()

    assert result["status"] == "insufficient"
    assert result["inserted"] == 1
    assert "required at least 2" in result["error"]
    assert result["diagnosis_path"] == "low-yield-query -> insufficient-new-records"
    with get_connection(read_only=True) as con:
        row = con.execute(
            "SELECT status, downloaded_count, inserted_count, diagnosis_path, error_message FROM core_ingestion_runs WHERE run_id = ?",
            [result["run_id"]],
        ).fetchone()
    assert row == (
        "insufficient",
        1,
        1,
        "low-yield-query -> insufficient-new-records",
        "Insufficient CORE collection: inserted 1 records; required at least 2. Diagnosis path: low-yield-query -> insufficient-new-records.",
    )


def test_default_core_query_targets_catalyst_scaffold_and_since_window() -> None:
    query = DEFAULT_QUERY.format(since="2026-05-31", year=2026)

    assert "catalyst" in query
    assert "scaffold" in query
    assert "publishedDate>=2026-05-31" in query
    assert "yearPublished:2026" not in query
    assert " OR molecule)" not in query


def test_publication_relevance_accepts_catalyst_scaffold_and_rejects_broad_noise() -> None:
    relevant_score, relevant_level = publication_relevance(
        "Pyridine ligand scaffold enables nickel cross-coupling catalysis",
        "Synthetic chemistry study of heterocyclic catalysts and reaction mechanism.",
        "ACS Catalysis",
        "chemistry, catalysis",
    )
    noise_score, noise_level = publication_relevance(
        "Virtual reality education and social media tourism",
        "A pedagogy paper mentioning molecule as a metaphor.",
        "Education Review",
        "teaching",
    )

    assert relevant_score >= 70
    assert relevant_level == "High relevance"
    assert noise_score < 40
    assert noise_level in {"Low relevance", "Off-topic"}


def test_core_publication_agent_filters_irrelevant_core_results(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    class MixedCoreClient(FakeCoreClient):
        def search_works(self, *args, **kwargs) -> list[dict]:
            self.calls.append({"query": args[0] if args else kwargs["query"], "limit": kwargs.get("limit"), "offset": kwargs.get("offset", 0)})
            if kwargs.get("offset", 0) > 0:
                return []
            return [
                {
                    "id": "core-noise",
                    "title": "Social media education study",
                    "sourceName": "Teaching Quarterly",
                    "abstract": "A tourism pedagogy paper that only mentions molecule as a metaphor.",
                    "topics": ["education"],
                },
                {
                    "id": "core-catalyst",
                    "title": "Indole scaffold catalysis for synthetic chemistry",
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "Catalyst design for heterocycle synthesis and reaction optimization.",
                    "topics": ["chemistry", "catalysis"],
                },
            ]

    client = MixedCoreClient()
    agent = CorePublicationAgent(client, CorePublicationAgentSettings(query="chemistry", daily_limit=5, page_size=2, min_inserted_success=1))

    result = agent.run_once()
    recent = CorePublicationRepository.recent_publications(limit=5)

    assert result["inserted"] == 1
    assert [item["title"] for item in recent] == ["Indole scaffold catalysis for synthetic chemistry"]
    assert is_ingestion_relevant({"title": recent[0]["title"], "abstract": recent[0]["summary"], "journal": recent[0]["journal"]})


def test_core_publication_agent_falls_back_to_older_publication_dates(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        CorePublicationRepository,
        "latest_successful_run_started_at",
        staticmethod(lambda: datetime(2026, 6, 5, tzinfo=timezone.utc)),
    )

    class FallbackCoreClient(FakeCoreClient):
        def search_works(self, query: str, limit: int, offset: int = 0, entity_type: str = "journal-article", sort: str = "") -> list[dict]:
            self.calls.append({"query": query, "limit": limit, "offset": offset, "entity_type": entity_type, "sort": sort})
            if "publishedDate>=2026-06-06" in query:
                return []
            return [
                {
                    "id": "core-fallback",
                    "title": "Photocatalysis scaffold for synthetic chemistry",
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "Catalytic reaction mechanism and heterocycle synthesis.",
                    "topics": ["chemistry", "catalysis"],
                    "publishedDate": "2026-06-01",
                    "yearPublished": 2026,
                }
            ]

    client = FallbackCoreClient()
    agent = CorePublicationAgent(
        client,
        CorePublicationAgentSettings(
            query="chemistry AND publishedDate>={since}",
            daily_limit=5,
            page_size=2,
            fallback_lookback_days=7,
            fallback_step_days=7,
            min_inserted_success=1,
        ),
    )

    result = agent.run_once()

    assert result["inserted"] == 1
    assert result["downloaded"] == 1
    assert result["query"] == "chemistry AND publishedDate>=2026-05-30"
    assert result["attempted_queries"] == [
        "chemistry AND publishedDate>=2026-06-06",
        "chemistry AND publishedDate>=2026-05-30",
    ]
    assert [call["query"] for call in client.calls] == result["attempted_queries"]
    with get_connection(read_only=True) as con:
        run_query = con.execute("SELECT query FROM core_ingestion_runs WHERE run_id = ?", [result["run_id"]]).fetchone()[0]
    assert run_query == "chemistry AND publishedDate>=2026-05-30"


def test_core_publication_agent_uses_year_query_after_empty_date_fallback(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        CorePublicationRepository,
        "latest_successful_run_started_at",
        staticmethod(lambda: datetime(2026, 6, 5, tzinfo=timezone.utc)),
    )

    class YearFallbackClient(FakeCoreClient):
        def search_works(self, query: str, limit: int, offset: int = 0, entity_type: str = "journal-article", sort: str = "") -> list[dict]:
            self.calls.append({"query": query, "limit": limit, "offset": offset, "entity_type": entity_type, "sort": sort})
            if "yearPublished:2026" not in query:
                return []
            return [
                {
                    "id": "core-year-fallback",
                    "title": "Ligand scaffold catalysis in synthetic chemistry",
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "Catalyst and reaction mechanism study for heterocycle synthesis.",
                    "topics": ["chemistry", "catalysis"],
                    "yearPublished": 2026,
                }
            ]

    client = YearFallbackClient()
    agent = CorePublicationAgent(
        client,
        CorePublicationAgentSettings(
            query="chemistry AND publishedDate>={since}",
            daily_limit=5,
            page_size=2,
            fallback_lookback_days=7,
            fallback_step_days=7,
            empty_result_fallback_query="chemistry AND yearPublished:{year}",
            min_inserted_success=1,
        ),
    )

    result = agent.run_once()

    assert result["inserted"] == 1
    assert result["query"] == "chemistry AND yearPublished:2026"
    assert result["attempted_queries"] == [
        "chemistry AND publishedDate>=2026-06-06",
        "chemistry AND publishedDate>=2026-05-30",
        "chemistry AND yearPublished:2026",
    ]


def test_core_publication_agent_marks_broad_query_fallback_insufficient(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        CorePublicationRepository,
        "latest_successful_run_started_at",
        staticmethod(lambda: datetime(2026, 6, 5, tzinfo=timezone.utc)),
    )

    class YearFallbackClient(FakeCoreClient):
        def search_works(self, query: str, limit: int, offset: int = 0, entity_type: str = "journal-article", sort: str = "") -> list[dict]:
            self.calls.append({"query": query, "limit": limit, "offset": offset, "entity_type": entity_type, "sort": sort})
            if "yearPublished:2026" not in query:
                return []
            return [
                {
                    "id": "core-year-fallback-insufficient",
                    "title": "Single broad fallback chemistry result",
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "Catalyst and reaction mechanism study.",
                    "topics": ["chemistry", "catalysis"],
                    "yearPublished": 2026,
                }
            ]

    result = CorePublicationAgent(
        YearFallbackClient(),
        CorePublicationAgentSettings(
            query="chemistry AND publishedDate>={since}",
            daily_limit=5,
            page_size=2,
            fallback_lookback_days=7,
            fallback_step_days=7,
            empty_result_fallback_query="chemistry AND yearPublished:{year}",
            min_inserted_success=2,
        ),
    ).run_once()

    assert result["status"] == "insufficient"
    assert result["diagnosis_path"] == "broad-query-fallback -> insufficient-new-records"


def test_core_publication_agent_marks_duplicate_heavy_insufficient(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    ensure_core_ingestion_schema()
    CorePublicationRepository.upsert_publications(
        [
            {
                "core_id": "duplicate-core-id",
                "title": "Existing chemistry publication",
                "doi": "10.1000/duplicate",
                "year_published": 2026,
                "published_date": "2026-06-01",
                "authors": ["Ada Chemist"],
                "journal": "Journal of Useful Chemistry",
                "abstract": "Existing catalyst paper.",
                "topics": ["chemistry"],
                "full_text_url": None,
                "source_url": None,
                "raw": {"id": "duplicate-core-id"},
            }
        ],
        "chemistry",
    )

    class DuplicateHeavyClient(FakeCoreClient):
        def search_works(self, query: str, limit: int, offset: int = 0, entity_type: str = "journal-article", sort: str = "") -> list[dict]:
            self.calls.append({"query": query, "limit": limit, "offset": offset, "entity_type": entity_type, "sort": sort})
            if offset > 0:
                return []
            return [
                {
                    "id": "duplicate-core-id",
                    "title": "Existing chemistry publication",
                    "doi": "10.1000/duplicate",
                    "yearPublished": 2026,
                    "authors": [{"name": "Ada Chemist"}],
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "Existing catalyst paper.",
                    "topics": ["chemistry"],
                }
            ]

    result = CorePublicationAgent(
        DuplicateHeavyClient(),
        CorePublicationAgentSettings(query="chemistry", daily_limit=5, page_size=2, min_inserted_success=1),
    ).run_once()

    assert result["status"] == "insufficient"
    assert result["downloaded"] == 0
    assert result["diagnosis_path"] == "duplicate-heavy-results -> insufficient-new-records"


def test_core_publication_agent_stops_when_saved_frontier_cursor_is_reached(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    ensure_core_ingestion_schema()
    CorePublicationRepository.upsert_ingestion_cursor(
        "core",
        frontier_core_id="frontier-core-id",
        frontier_published_date="2026-06-10",
        query="chemistry AND publishedDate>=2026-06-03",
    )

    class CursorClient(FakeCoreClient):
        def search_works(self, query: str, limit: int, offset: int = 0, entity_type: str = "journal-article", sort: str = "") -> list[dict]:
            self.calls.append({"query": query, "limit": limit, "offset": offset, "entity_type": entity_type, "sort": sort})
            if offset > 0:
                return []
            return [
                {
                    "id": "new-core-id",
                    "title": "Fresh catalyst discovery",
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "A new catalytic chemistry result.",
                    "topics": ["chemistry"],
                    "publishedDate": "2026-06-11",
                    "yearPublished": 2026,
                },
                {
                    "id": "frontier-core-id",
                    "title": "Previously scanned frontier record",
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "An older catalyst chemistry result.",
                    "topics": ["chemistry"],
                    "publishedDate": "2026-06-10",
                    "yearPublished": 2026,
                },
                {
                    "id": "older-core-id",
                    "title": "Older chemistry result that should not be reached",
                    "sourceName": "Journal of Useful Chemistry",
                    "abstract": "This should never be scanned once the frontier is hit.",
                    "topics": ["chemistry"],
                    "publishedDate": "2026-06-09",
                    "yearPublished": 2026,
                },
            ]

    result = CorePublicationAgent(
        CursorClient(),
        CorePublicationAgentSettings(query="chemistry AND publishedDate>={since}", daily_limit=5, page_size=5, min_inserted_success=1),
    ).run_once()

    cursor = CorePublicationRepository.ingestion_cursor()

    assert result["status"] == "succeeded"
    assert result["downloaded"] == 1
    assert result["inserted"] == 1
    assert result["query"] == "chemistry AND publishedDate>=2026-06-03"
    assert cursor is not None
    assert cursor["frontier_core_id"] == "new-core-id"
    assert cursor["frontier_published_date"] == "2026-06-11"


def test_core_publication_agent_advances_since_date_after_latest_success(monkeypatch) -> None:
    latest_success = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    now = datetime(2026, 6, 11, 9, 30, tzinfo=timezone.utc)

    monkeypatch.setattr(
        CorePublicationRepository,
        "ingestion_cursor",
        staticmethod(lambda source="core": None),
    )
    monkeypatch.setattr(
        CorePublicationRepository,
        "latest_successful_run_started_at",
        staticmethod(lambda: latest_success),
    )

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(core_agent_module, "datetime", FixedDateTime)

    agent = CorePublicationAgent(FakeCoreClient(), CorePublicationAgentSettings(query="chemistry AND publishedDate>={since}"))

    assert agent._since_date().date().isoformat() == "2026-06-06"


def test_core_publication_agent_uses_cursor_overlap_for_since_date(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    CorePublicationRepository.upsert_ingestion_cursor(
        "core",
        frontier_core_id="cursor-core-id",
        frontier_published_date="2026-06-09",
        query="chemistry AND publishedDate>=2026-06-02",
    )
    now = datetime(2026, 6, 11, 9, 30, tzinfo=timezone.utc)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(core_agent_module, "datetime", FixedDateTime)

    agent = CorePublicationAgent(
        FakeCoreClient(),
        CorePublicationAgentSettings(query="chemistry AND publishedDate>={since}", cursor_overlap_days=2),
    )

    assert agent._since_date().date().isoformat() == "2026-06-07"


def test_settings_from_env_uses_configured_key_without_printable_secret(monkeypatch) -> None:
    monkeypatch.setattr(core_agent_module, "is_api_key_configured", lambda: True)
    monkeypatch.setattr(core_agent_module, "get_secret_env", lambda name, default="": default)
    monkeypatch.setattr(core_agent_module, "get_config", lambda: type("Config", (), {"literature_api_key": "SECRET_CORE_KEY"})())

    api_settings, agent_settings = settings_from_env()

    assert api_settings.api_key == "SECRET_CORE_KEY"
    assert "SECRET_CORE_KEY" not in {
        "base_url": api_settings.base_url,
        "query": agent_settings.query,
        "entity_type": agent_settings.entity_type,
        "sort": agent_settings.sort,
    }.values()
    assert agent_settings.min_inserted_success == 15


def test_settings_from_env_migrates_legacy_default_query(monkeypatch) -> None:
    monkeypatch.setattr(core_agent_module, "is_api_key_configured", lambda: True)
    monkeypatch.setattr(core_agent_module, "get_config", lambda: type("Config", (), {"literature_api_key": "SECRET_CORE_KEY"})())
    monkeypatch.delenv("CHEMPULSE_CORE_QUERY", raising=False)

    def fake_env(name: str, default: str = "") -> str:
        if name == "CHEMPULSE_CORE_QUERY":
            return core_agent_module.LEGACY_DEFAULT_QUERY
        return default

    monkeypatch.setattr(core_agent_module, "get_secret_env", fake_env)

    _, agent_settings = settings_from_env()

    assert agent_settings.query == DEFAULT_QUERY


def test_settings_from_env_migrates_legacy_process_query_override(monkeypatch) -> None:
    monkeypatch.setattr(core_agent_module, "is_api_key_configured", lambda: True)
    monkeypatch.setattr(core_agent_module, "get_config", lambda: type("Config", (), {"literature_api_key": "SECRET_CORE_KEY"})())
    monkeypatch.setenv("CHEMPULSE_CORE_QUERY", core_agent_module.LEGACY_DEFAULT_QUERY)
    monkeypatch.setattr(core_agent_module, "get_secret_env", lambda name, default="": default)

    _, agent_settings = settings_from_env()

    assert agent_settings.query == DEFAULT_QUERY


def test_settings_from_env_honors_custom_process_query_override(monkeypatch) -> None:
    monkeypatch.setattr(core_agent_module, "is_api_key_configured", lambda: True)
    monkeypatch.setattr(core_agent_module, "get_config", lambda: type("Config", (), {"literature_api_key": "SECRET_CORE_KEY"})())
    monkeypatch.setenv("CHEMPULSE_CORE_QUERY", 'chemistry AND publishedDate>={since}')
    monkeypatch.setattr(core_agent_module, "get_secret_env", lambda name, default="": default)

    _, agent_settings = settings_from_env()

    assert agent_settings.query == 'chemistry AND publishedDate>={since}'


def test_settings_from_env_fails_gracefully_when_key_missing(monkeypatch) -> None:
    monkeypatch.setattr(core_agent_module, "is_api_key_configured", lambda: False)

    try:
        settings_from_env()
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("settings_from_env should fail when CORE_API_KEY is missing")

    assert "CORE_API_KEY is not set" in message
