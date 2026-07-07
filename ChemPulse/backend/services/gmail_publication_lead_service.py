from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import requests

from backend.config import get_secret_env
from backend.data.manual_publication_importer import extract_quick_publication_leads, normalize_quick_publication_lead

GMAIL_ACCESS_TOKEN_ENV = "CHEMPULSE_GMAIL_ACCESS_TOKEN"
GMAIL_CLIENT_ID_ENV = "CHEMPULSE_GMAIL_CLIENT_ID"
GMAIL_CLIENT_SECRET_ENV = "CHEMPULSE_GMAIL_CLIENT_SECRET"
GMAIL_REFRESH_TOKEN_ENV = "CHEMPULSE_GMAIL_REFRESH_TOKEN"
GMAIL_QUERY_ENV = "CHEMPULSE_GMAIL_QUERY"
DEFAULT_GMAIL_QUERY = "newer_than:30d academia recommendation"
GMAIL_API_BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
REQUEST_TIMEOUT_SECONDS = 15


class GmailPublicationLeadService:
    @staticmethod
    def configuration_hint() -> str:
        if GmailPublicationLeadService.is_configured():
            return "[configured]"
        return (
            "Set CHEMPULSE_GMAIL_ACCESS_TOKEN or the "
            "CHEMPULSE_GMAIL_CLIENT_ID / CHEMPULSE_GMAIL_CLIENT_SECRET / "
            "CHEMPULSE_GMAIL_REFRESH_TOKEN trio."
        )

    @staticmethod
    def is_configured() -> bool:
        if get_secret_env(GMAIL_ACCESS_TOKEN_ENV).strip():
            return True
        return all(
            get_secret_env(env_name).strip()
            for env_name in (GMAIL_CLIENT_ID_ENV, GMAIL_CLIENT_SECRET_ENV, GMAIL_REFRESH_TOKEN_ENV)
        )

    @staticmethod
    def fetch_recent_academia_recommendations(limit: int = 6, query: str = "") -> dict[str, Any]:
        if not GmailPublicationLeadService.is_configured():
            raise RuntimeError(GmailPublicationLeadService.configuration_hint())

        effective_query = query.strip() or os.getenv(GMAIL_QUERY_ENV, DEFAULT_GMAIL_QUERY).strip() or DEFAULT_GMAIL_QUERY
        access_token = _gmail_access_token()
        message_refs = _list_message_refs(access_token, effective_query, max(limit * 3, limit))
        leads: list[dict[str, Any]] = []
        seen_sources: set[str] = set()
        warnings: list[str] = []

        for ref in message_refs:
            payload = _gmail_get(
                f"{GMAIL_API_BASE_URL}/messages/{ref['id']}",
                access_token=access_token,
                params={"format": "full"},
            ).json()
            message_leads = _message_leads(payload, effective_query, seen_sources)
            if not message_leads:
                continue
            leads.extend(message_leads)
            if len(leads) >= limit:
                break

        if not leads and not warnings:
            warnings.append("No recent Academia recommendation links with DOI/article leads were found.")

        return {
            "query": effective_query,
            "items": leads[:limit],
            "warnings": warnings,
        }


def _gmail_access_token(force_refresh: bool = False) -> str:
    access_token = get_secret_env(GMAIL_ACCESS_TOKEN_ENV).strip()
    if access_token and not force_refresh:
        return access_token

    client_id = get_secret_env(GMAIL_CLIENT_ID_ENV).strip()
    client_secret = get_secret_env(GMAIL_CLIENT_SECRET_ENV).strip()
    refresh_token = get_secret_env(GMAIL_REFRESH_TOKEN_ENV).strip()
    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError(GmailPublicationLeadService.configuration_hint())

    response = requests.post(
        GMAIL_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    token = str(response.json().get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Gmail token refresh succeeded without returning an access token.")
    return token


def _gmail_get(url: str, *, access_token: str, params: dict[str, Any] | None = None) -> requests.Response:
    response = requests.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 401 and get_secret_env(GMAIL_REFRESH_TOKEN_ENV).strip():
        refreshed_token = _gmail_access_token(force_refresh=True)
        response = requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {refreshed_token}"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    response.raise_for_status()
    return response


def _list_message_refs(access_token: str, query: str, limit: int) -> list[dict[str, str]]:
    response = _gmail_get(
        f"{GMAIL_API_BASE_URL}/messages",
        access_token=access_token,
        params={"q": query, "maxResults": min(max(limit, 1), 25)},
    )
    return list(response.json().get("messages") or [])


def _message_leads(message: dict[str, Any], query: str, seen_sources: set[str]) -> list[dict[str, Any]]:
    payload = message.get("payload") or {}
    headers = _header_map(payload.get("headers") or [])
    subject = headers.get("subject", "")
    sender = headers.get("from", "")
    snippet = str(message.get("snippet") or "")
    body_text = _message_text(payload)
    received_at = _received_at(headers.get("date", ""), message.get("internalDate"))
    leads: list[dict[str, Any]] = []
    seen_publications: set[str] = set()

    for index, candidate in enumerate(_rank_candidates(extract_quick_publication_leads("\n".join([subject, snippet, body_text]))), start=1):
        if candidate in seen_sources:
            continue
        try:
            normalized = normalize_quick_publication_lead(candidate)
        except Exception:
            continue
        publication = normalized.get("publication", {})
        publication_key = str(publication.get("doi") or publication.get("source_url") or candidate).lower()
        if publication_key in seen_publications:
            continue
        seen_sources.add(candidate)
        seen_publications.add(publication_key)
        leads.append(
            {
                "lead_id": f"{message.get('id', 'message')}:{index}",
                "lead_source": candidate,
                "title": publication.get("title") or subject or "Untitled recommendation",
                "doi": publication.get("doi") or "",
                "journal": publication.get("journal") or "External literature lead",
                "year": str(publication.get("year_published") or "n/a"),
                "authors": ", ".join(publication.get("authors") or []) or "Unknown authors",
                "message_id": str(message.get("id") or ""),
                "thread_id": str(message.get("threadId") or ""),
                "subject": subject or "Academia recommendation",
                "sender": sender or "Unknown sender",
                "received_at": received_at,
                "snippet": snippet,
                "query": query,
                "provenance_label": f"{sender or 'Unknown sender'} | {received_at or 'Unknown time'}",
            }
        )
    return leads


def _rank_candidates(candidates: list[str]) -> list[str]:
    def score(candidate: str) -> int:
        lowered = candidate.lower()
        value = 0
        if lowered.startswith("10."):
            value += 100
        if "doi.org" in lowered:
            value += 90
        if "academia" in lowered:
            value += 70
        if any(term in lowered for term in ("unsubscribe", "preferences", "settings", "privacy", "support")):
            value -= 120
        return value

    return sorted(candidates, key=score, reverse=True)


def _header_map(headers: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(header.get("name") or "").strip().lower(): str(header.get("value") or "").strip()
        for header in headers
        if header.get("name")
    }


def _message_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime_type = str(part.get("mimeType") or "").lower()
        body = part.get("body") or {}
        data = str(body.get("data") or "")
        if data and mime_type.startswith("text/"):
            decoded = _decode_body(data)
            if decoded:
                chunks.append(decoded)
        for child in part.get("parts") or []:
            if isinstance(child, dict):
                walk(child)

    walk(payload)
    return "\n".join(chunks)


def _decode_body(value: str) -> str:
    padded = value + "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _received_at(date_header: str, internal_date: Any) -> str:
    if date_header:
        try:
            parsed = parsedate_to_datetime(date_header)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, IndexError):
            pass
    try:
        millis = int(str(internal_date or "0"))
        if millis > 0:
            return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).isoformat()
    except ValueError:
        return ""
    return ""
