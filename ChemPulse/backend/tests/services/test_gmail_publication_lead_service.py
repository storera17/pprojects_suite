from __future__ import annotations

import base64

from backend.services.gmail_publication_lead_service import GmailPublicationLeadService


class _FakeResponse:
    def __init__(self, payload=None, status_code: int = 200) -> None:
        self._payload = payload or {}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_fetch_recent_academia_recommendations_returns_normalized_leads(monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_GMAIL_ACCESS_TOKEN", "test-token")

    encoded_body = base64.urlsafe_b64encode(
        b"https://click.academia.edu/redirect?url=https%3A%2F%2Fdoi.org%2F10.1055%252Fs-0029-1218837"
    ).decode("utf-8")

    def fake_get(url, params=None, headers=None, timeout=None):
        assert headers["Authorization"] == "Bearer test-token"
        if url.endswith("/messages"):
            assert params["q"] == "newer_than:30d academia recommendation"
            return _FakeResponse({"messages": [{"id": "msg-1", "threadId": "thread-1"}]})
        if url.endswith("/messages/msg-1"):
            return _FakeResponse(
                {
                    "id": "msg-1",
                    "threadId": "thread-1",
                    "snippet": "Academia recommendation",
                    "internalDate": "1780000000000",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Recommended paper"},
                            {"name": "From", "value": "updates@academia-mail.com"},
                            {"name": "Date", "value": "Sat, 13 Jun 2026 08:00:00 -0400"},
                        ],
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {"data": encoded_body},
                            }
                        ],
                    },
                }
            )
        raise AssertionError(url)

    monkeypatch.setattr("backend.services.gmail_publication_lead_service.requests.get", fake_get)
    monkeypatch.setattr(
        "backend.services.gmail_publication_lead_service.normalize_quick_publication_lead",
        lambda candidate: {
            "publication": {
                "title": "Synthesis of New Dicationic Azolium Salts",
                "doi": "10.1055/s-0029-1218837",
                "journal": "Synthesis",
                "year_published": 2010,
                "authors": ["Sadaf Sadiq Khan", "Jurgen Liebscher"],
            }
        },
    )

    result = GmailPublicationLeadService.fetch_recent_academia_recommendations(limit=3)

    assert result["query"] == "newer_than:30d academia recommendation"
    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "Synthesis of New Dicationic Azolium Salts"
    assert result["items"][0]["doi"] == "10.1055/s-0029-1218837"
    assert result["items"][0]["sender"] == "updates@academia-mail.com"
    assert result["items"][0]["message_id"] == "msg-1"


def test_fetch_recent_academia_recommendations_requires_configuration(monkeypatch) -> None:
    monkeypatch.delenv("CHEMPULSE_GMAIL_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("CHEMPULSE_GMAIL_CLIENT_ID", raising=False)
    monkeypatch.delenv("CHEMPULSE_GMAIL_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("CHEMPULSE_GMAIL_REFRESH_TOKEN", raising=False)

    try:
        GmailPublicationLeadService.fetch_recent_academia_recommendations(limit=1)
    except RuntimeError as exc:
        assert "CHEMPULSE_GMAIL_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected Gmail configuration error")

