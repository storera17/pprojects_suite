from __future__ import annotations

import requests

from backend.integrations.core_api import CoreApiClient, CoreApiError, CoreApiSettings
import backend.integrations.core_api as core_api_module


class _FakeResponse:
    def __init__(self, payload: dict, *, status_code: int = 200, ok: bool = True, headers: dict[str, str] | None = None):
        self._payload = payload
        self.status_code = status_code
        self.ok = ok
        self.headers = headers or {}
        self.text = ""

    def json(self) -> dict:
        return self._payload


def test_core_api_retries_transient_request_exceptions(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.exceptions.SSLError("unexpected eof")
        return _FakeResponse({"results": [{"id": "1", "title": "Recovered result"}]})

    monkeypatch.setattr(core_api_module.requests, "get", fake_get)

    client = CoreApiClient(CoreApiSettings(api_key="test-key", request_interval_seconds=0.0, max_retries=2))
    results = client.search_works("chemistry", limit=1)

    assert calls["count"] == 2
    assert results == [{"id": "1", "title": "Recovered result"}]


def test_core_api_raises_clean_error_after_retry_exhaustion(monkeypatch) -> None:
    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("temporary network failure")

    monkeypatch.setattr(core_api_module.requests, "get", fake_get)

    client = CoreApiClient(CoreApiSettings(api_key="test-key", request_interval_seconds=0.0, max_retries=2))

    try:
        client.search_works("chemistry", limit=1)
    except CoreApiError as exc:
        assert "CORE API request failed:" in str(exc)
        assert "temporary network failure" in str(exc)
    else:
        raise AssertionError("Expected CoreApiError after retries were exhausted.")
