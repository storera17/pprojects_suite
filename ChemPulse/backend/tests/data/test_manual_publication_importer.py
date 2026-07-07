from __future__ import annotations

import csv
import json

from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.manual_publication_importer import (
    extract_quick_publication_leads,
    import_manual_publications,
    import_quick_publication_lead,
    import_quick_publication_leads,
    normalize_quick_publication_lead,
)
from frontend.state.app_state import AppState
from frontend.ui.pages.dashboard import dashboard_page


class _FakeResponse:
    def __init__(self, payload=None, text: str = "") -> None:
        self._payload = payload or {}
        self.text = text

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_import_manual_publication_folder_recursively(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "storage"))
    import_root = tmp_path / "imports"
    nested = import_root / "nested"
    nested.mkdir(parents=True)

    csv_path = import_root / "papers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["title", "doi", "journal", "year", "authors", "keywords"])
        writer.writeheader()
        writer.writerow(
            {
                "title": "Manual catalyst paper",
                "doi": "10.2000/manual",
                "journal": "Personal Library",
                "year": "2026",
                "authors": "Ada Chemist; Linus Lab",
                "keywords": "catalyst; synthesis",
            }
        )

    json_path = nested / "more_papers.json"
    json_path.write_text(
        json.dumps(
            [
                {
                    "title": "Folder imported scaffold",
                    "journal": "Lab Notes",
                    "publication_year": 2025,
                    "url": "https://example.test/paper",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = import_manual_publications(import_root)
    metrics = CorePublicationRepository.publication_metrics()
    recent = CorePublicationRepository.recent_publications(limit=5, query="manual")

    assert result.scanned_files == 2
    assert result.parsed_records == 2
    assert result.inserted == 2
    assert result.updated == 0
    assert result.skipped == 0
    assert result.report_path.endswith(".md")
    assert metrics["publication_count"] == 2
    assert any(item["title"] == "Manual catalyst paper" for item in recent)


def test_quick_import_academia_recommendation_doi(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "storage"))

    def fake_get(url, **_kwargs):
        assert "10.1055%2Fs-0029-1218837" in url
        return _FakeResponse(
            {
                "message": {
                    "DOI": "10.1055/s-0029-1218837",
                    "title": ["Synthesis of New Dicationic Azolium Salts and Their Application as NHC Precursors in Suzuki-Miyaura Coupling"],
                    "container-title": ["Synthesis"],
                    "author": [{"given": "Sadaf Sadiq", "family": "Khan"}, {"given": "Jurgen", "family": "Liebscher"}],
                    "published-online": {"date-parts": [[2010, 6, 25]]},
                    "subject": ["catalysis", "organic chemistry"],
                    "URL": "https://doi.org/10.1055/s-0029-1218837",
                }
            }
        )

    monkeypatch.setattr("backend.data.manual_publication_importer.requests.get", fake_get)

    result = import_manual_publications("10.1055/s-0029-1218837")
    recent = CorePublicationRepository.recent_publications(limit=3, query="azolium")

    assert result.import_type == "quick"
    assert result.scanned_files == 0
    assert result.parsed_records == 1
    assert result.inserted == 1
    assert result.updated == 0
    assert "manual-publication-import" in result.report_path
    assert recent[0]["doi"] == "10.1055/s-0029-1218837"
    assert recent[0]["journal"] == "Synthesis"
    assert "Suzuki-Miyaura" in recent[0]["title"]


def test_quick_import_extracts_doi_from_encoded_email_link(monkeypatch) -> None:
    def fake_get(url, **_kwargs):
        assert url.endswith("10.1055%2Fs-0029-1218837")
        return _FakeResponse(
            {
                "message": {
                    "DOI": "10.1055/s-0029-1218837",
                    "title": ["Synthesis of New Dicationic Azolium Salts and Their Application as NHC Precursors in Suzuki-Miyaura Coupling"],
                    "container-title": ["Synthesis"],
                    "issued": {"date-parts": [[2010]]},
                }
            }
        )

    monkeypatch.setattr("backend.data.manual_publication_importer.requests.get", fake_get)

    normalized = normalize_quick_publication_lead(
        "https://click.academia.edu/redirect?url=https%3A%2F%2Fdoi.org%2F10.1055%252Fs-0029-1218837"
    )

    publication = normalized["publication"]
    assert normalized["input_kind"] == "doi"
    assert publication["core_id"] == "manual:doi:10.1055/s-0029-1218837"
    assert publication["doi"] == "10.1055/s-0029-1218837"
    assert publication["topics"] == ["Suzuki-Miyaura coupling", "NHC precursors", "azolium salts", "dicationic salts", "synthesis"]


def test_extract_quick_publication_leads_finds_encoded_academia_target() -> None:
    candidates = extract_quick_publication_leads(
        'Read more: https://click.academia.edu/redirect?url=https%3A%2F%2Fdoi.org%2F10.1055%252Fs-0029-1218837'
    )

    assert "https://click.academia.edu/redirect?url=https%3A%2F%2Fdoi.org%2F10.1055%252Fs-0029-1218837" in candidates
    assert "10.1055/s-0029-1218837" in candidates


def test_quick_import_report_includes_gmail_provenance(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "storage"))

    def fake_get(url, **_kwargs):
        assert url.endswith("10.1055%2Fs-0029-1218837")
        return _FakeResponse(
            {
                "message": {
                    "DOI": "10.1055/s-0029-1218837",
                    "title": ["Synthesis of New Dicationic Azolium Salts and Their Application as NHC Precursors in Suzuki-Miyaura Coupling"],
                    "container-title": ["Synthesis"],
                    "issued": {"date-parts": [[2010]]},
                }
            }
        )

    monkeypatch.setattr("backend.data.manual_publication_importer.requests.get", fake_get)

    result = import_quick_publication_lead(
        "https://click.academia.edu/redirect?url=https%3A%2F%2Fdoi.org%2F10.1055%252Fs-0029-1218837",
        provenance={
            "channel": "gmail",
            "provider": "Gmail",
            "query": "newer_than:30d academia recommendation",
            "sender": "updates@academia-mail.com",
            "subject": "Recommended paper for you",
            "received_at": "2026-06-13T12:00:00+00:00",
            "message_id": "gmail-message-123",
        },
    )

    report_text = (tmp_path / "storage" / "reports").glob("manual-publication-import-*.md")
    report_path = next(report_text)
    report = report_path.read_text(encoding="utf-8")

    assert result.inserted == 1
    assert "## Quick Import Provenance" in report
    assert "updates@academia-mail.com" in report
    assert "gmail-message-123" in report


def test_batch_quick_import_dedupes_duplicate_gmail_leads(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path / "storage"))

    def fake_normalize(raw_source: str, provenance=None):
        doi = "10.1000/duplicate" if "duplicate" in raw_source else "10.1000/unique"
        title = "Duplicate lead" if "duplicate" in raw_source else "Unique lead"
        return {
            "raw_source": raw_source,
            "canonical_source": doi,
            "input_kind": "doi",
            "metadata_source": "test",
            "provenance": provenance or {},
            "warnings": [],
            "publication": {
                "core_id": f"manual:doi:{doi}",
                "title": title,
                "doi": doi,
                "journal": "Synthesis",
                "year_published": 2026,
                "authors": ["Ada Chemist"],
                "topics": ["catalysis"],
                "source_url": f"https://doi.org/{doi}",
                "full_text_url": f"https://doi.org/{doi}",
                "raw": {"provenance": provenance or {}},
            },
        }

    monkeypatch.setattr("backend.data.manual_publication_importer.normalize_quick_publication_lead", fake_normalize)

    result = import_quick_publication_leads(
        [
            {"raw_source": "https://lead.test/duplicate-1", "provenance": {"message_id": "msg-1", "sender": "a@test"}},
            {"raw_source": "https://lead.test/duplicate-2", "provenance": {"message_id": "msg-2", "sender": "b@test"}},
            {"raw_source": "https://lead.test/unique", "provenance": {"message_id": "msg-3", "sender": "c@test"}},
        ]
    )

    report_text = next((tmp_path / "storage" / "reports").glob("manual-publication-import-*.md")).read_text(encoding="utf-8")

    assert result.parsed_records == 2
    assert result.inserted == 2
    assert result.updated == 0
    assert result.skipped == 1
    assert any("duplicate quick-import lead" in warning for warning in result.errors)
    assert "## Quick Import Batch" in report_text
    assert "msg-1" in report_text
    assert "msg-3" in report_text


def test_app_state_batch_gmail_import_refreshes_dashboard_and_payload(monkeypatch) -> None:
    calls: dict[str, object] = {}
    state = object.__new__(AppState)
    for name, value in {
        "dirty_vars": set(),
        "dirty_substates": set(),
        "_backend_vars": {},
        "_was_touched": False,
        "_self_state": None,
        "substates": {},
        "parent_state": None,
    }.items():
        object.__setattr__(state, name, value)

    state.gmail_recommendation_leads = [
        {
            "lead_id": "lead-1",
            "lead_source": "https://lead.test/1",
            "query": "after:2026/6/15 academia recommendation",
            "sender": "updates@academia-mail.com",
            "subject": "Recommended paper",
            "received_at": "2026-06-15T12:00:00+00:00",
            "message_id": "msg-1",
            "thread_id": "thread-1",
        },
        {
            "lead_id": "lead-2",
            "lead_source": "https://lead.test/2",
            "query": "after:2026/6/15 academia recommendation",
            "sender": "updates@academia-mail.com",
            "subject": "Recommended paper 2",
            "received_at": "2026-06-15T13:00:00+00:00",
            "message_id": "msg-2",
            "thread_id": "thread-2",
        },
    ]
    state.manual_import_status = ""
    state.loading = False

    class _FakeResult:
        inserted = 1
        updated = 1
        skipped = 0
        report_path = "C:/tmp/report.md"
        errors: list[str] = []

    def fake_import(batch):
        calls["batch"] = batch
        return _FakeResult()

    monkeypatch.setattr("frontend.state.app_state.import_quick_publication_leads", fake_import)
    monkeypatch.setattr(AppState, "_refresh_dashboard_view", lambda self: calls.__setitem__("refreshed", True))
    state.import_all_gmail_publication_leads()

    batch = calls["batch"]
    assert isinstance(batch, list)
    assert len(batch) == 2
    assert batch[0]["provenance"]["message_id"] == "msg-1"
    assert batch[1]["provenance"]["thread_id"] == "thread-2"
    assert "Imported 1 new / 1 updated from 2 Gmail lead(s)." in state.manual_import_status
    assert calls["refreshed"] is True
    assert state.loading is False


def test_dashboard_page_renders_gmail_batch_import_action() -> None:
    rendered = str(dashboard_page().render())

    assert "Import All" in rendered
    assert "Pull Gmail Leads" in rendered
    assert "Import" in rendered
