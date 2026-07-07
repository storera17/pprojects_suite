from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests


class CoreApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class CoreApiSettings:
    api_key: str
    base_url: str = "https://api.core.ac.uk/v3"
    request_interval_seconds: float = 11.0
    timeout_seconds: float = 30.0
    max_retries: int = 3


class CoreApiClient:
    def __init__(self, settings: CoreApiSettings) -> None:
        self.settings = settings
        self._last_request_at = 0.0

    def search_works(
        self,
        query: str,
        limit: int,
        offset: int = 0,
        entity_type: str = "journal-article",
        sort: str = "",
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"q": query, "limit": limit, "offset": offset}
        if entity_type:
            params["entity_type"] = entity_type
        if sort:
            params["sort"] = sort

        payload = self._get("/search/works/", params)
        results = payload.get("results") or payload.get("data") or []
        if not isinstance(results, list):
            raise CoreApiError("CORE search response did not include a results list.")
        return results

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.settings.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Accept": "application/json",
            "User-Agent": "ChemPulse CORE daily ingestor",
        }

        for attempt in range(1, self.settings.max_retries + 1):
            self._respect_rate_limit()
            try:
                response = requests.get(url, headers=headers, params=params, timeout=self.settings.timeout_seconds)
            except requests.exceptions.RequestException as exc:
                if attempt < self.settings.max_retries and _is_transient_request_exception(exc):
                    time.sleep(self.settings.request_interval_seconds * attempt)
                    continue
                raise CoreApiError(f"CORE API request failed: {exc}") from exc
            if response.status_code == 429:
                retry_after = _retry_after_seconds(response)
                time.sleep(retry_after or self.settings.request_interval_seconds * attempt)
                continue
            if 500 <= response.status_code < 600 and attempt < self.settings.max_retries:
                time.sleep(self.settings.request_interval_seconds * attempt)
                continue
            if not response.ok:
                raise CoreApiError(f"CORE API returned HTTP {response.status_code}: {response.text[:300]}")
            try:
                return response.json()
            except ValueError as exc:
                raise CoreApiError("CORE API response was not valid JSON.") from exc

        raise CoreApiError("CORE API rate limit retries were exhausted.")

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait_seconds = self.settings.request_interval_seconds - elapsed
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        self._last_request_at = time.monotonic()


def normalize_core_work(work: dict[str, Any]) -> dict[str, Any] | None:
    core_id = work.get("id") or work.get("coreId") or work.get("core_id")
    title = work.get("title")
    if not core_id or not title:
        return None

    authors = _normalize_authors(work.get("authors") or work.get("contributors") or [])
    topics = work.get("topics") or work.get("subjects") or []
    if isinstance(topics, str):
        topics = [topics]

    return {
        "core_id": str(core_id),
        "title": str(title),
        "doi": _first_present(work, "doi", "DOI"),
        "year_published": _safe_int(_first_present(work, "yearPublished", "year")),
        "published_date": _first_present(work, "publishedDate", "published_date", "createdDate"),
        "authors": authors,
        "journal": _first_present(work, "sourceTitle", "sourceName", "publisher", "journal"),
        "abstract": _first_present(work, "abstract", "description"),
        "topics": topics,
        "full_text_url": _first_present(work, "downloadUrl", "fullTextLink", "pdfUrl"),
        "source_url": _first_present(work, "sourceFulltextUrls", "urls", "oaiPmhUrl"),
        "raw": work,
    }


def _normalize_authors(authors: list[Any]) -> list[str]:
    normalized: list[str] = []
    for author in authors:
        if isinstance(author, str):
            normalized.append(author)
        elif isinstance(author, dict):
            name = author.get("name") or author.get("fullName") or author.get("displayName")
            if name:
                normalized.append(str(name))
    return normalized


def _first_present(source: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if isinstance(value, list):
            return value[0] if value else None
        if value not in (None, ""):
            return value
    return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _retry_after_seconds(response: requests.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _is_transient_request_exception(exc: requests.exceptions.RequestException) -> bool:
    return isinstance(
        exc,
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.SSLError,
            requests.exceptions.ChunkedEncodingError,
        ),
    )