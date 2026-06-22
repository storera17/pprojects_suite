from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import requests

from app.core.config import settings
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import cache_snapshot

DUMMY_PREFIXES = ("dummy", "your_", "paste_", "<")


def is_configured(value: str | None) -> bool:
    if value is None:
        return False
    clean = str(value).strip()
    if not clean:
        return False
    lower = clean.lower()
    if lower in {"none", "null", "changeme", "replace_me", "todo"}:
        return False
    return not lower.startswith(DUMMY_PREFIXES)


def classify_provider_error(text: str) -> str:
    lower = (text or "").lower()
    if any(term in lower for term in ["429", "rate limit", "rate_limited", "too many requests", "call frequency", "premium endpoint"]):
        return "rate_limited"
    if any(term in lower for term in ["405", "method not allowed"]):
        return "method_not_allowed"
    if any(term in lower for term in ["401", "403", "unauthorized", "forbidden", "invalid api key", "invalid token", "api key", "authentication"]):
        return "auth_error"
    if any(term in lower for term in ["not entitled", "entitlement", "subscription", "permission", "plan"]):
        return "not_entitled"
    return "error"


def request_json(provider: str, method: str, url: str, **kwargs) -> tuple[dict | list | None, str | None, str]:
    try:
        response = requests.request(method, url, timeout=kwargs.pop("timeout", 25), **kwargs)
        text = response.text[:500]
        if response.status_code == 429:
            return None, f"Rate limit reached: {text}", "rate_limited"
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and payload.get("error"):
            error = payload.get("error")
            message = error.get("info") if isinstance(error, dict) else str(error)
            return payload, message, classify_provider_error(message)
        return payload, None, "ok"
    except Exception as exc:
        return None, str(exc), classify_provider_error(str(exc))


class BaseCachedProvider:
    provider_name: str = ""

    def _today(self) -> date:
        return datetime.now(timezone.utc).date()

    def _iso_day_from_ms(self, ms: int | float | None) -> str | None:
        if not ms:
            return None
        try:
            return datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc).date().isoformat()
        except Exception:
            return None

    def _float(self, value: Any) -> float | None:
        try:
            if value in (None, "", "."):
                return None
            return float(value)
        except Exception:
            return None

    def _ttl_seconds(self) -> int:
        try:
            return int(settings.provider_cache_ttl_seconds)
        except Exception:
            return 86400

    def _format_cache_age(self, snapshot: dict[str, Any]) -> str:
        minutes = snapshot.get("cache_age_minutes")
        if minutes is None:
            return "unknown age"
        if minutes < 60:
            return f"{minutes:.1f} min old"
        return f"{minutes / 60:.1f} hr old"

    def _status_raw(
        self,
        source: str,
        snapshot: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
        rate_limit_fallback: bool = False,
        fallback_active: bool = False,
        provider_error_status: str | None = None,
        provider_error_message: str | None = None,
    ) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "source": source,
            "cache_source": source,
            "rate_limit_fallback": rate_limit_fallback,
            "fallback_active": fallback_active,
        }
        if snapshot:
            raw.update(
                {
                    "cache_record_count": snapshot.get("count"),
                    "cache_ttl_seconds": self._ttl_seconds(),
                    "cache_age_seconds": snapshot.get("cache_age_seconds"),
                    "cache_age_minutes": snapshot.get("cache_age_minutes"),
                    "cache_fresh": snapshot.get("fresh"),
                    "cache_collected_at": snapshot.get("cache_collected_at"),
                }
            )
        if extra:
            raw.update(extra)
        if provider_error_status:
            raw["provider_error_status"] = provider_error_status
        if provider_error_message:
            raw["provider_error_message"] = provider_error_message
        return raw

    def _fresh_cache_result(
        self,
        category: str | None,
        symbol: str | None,
        limit: int,
        label: str,
    ) -> dict[str, Any] | None:
        snapshot = cache_snapshot(self.provider_name, category, symbol, ttl_seconds=self._ttl_seconds(), limit=limit)
        if not snapshot.get("fresh"):
            return None
        message = (
            f"Using fresh SQLite cache for {label}: {snapshot['count']} rows "
            f"({self._format_cache_age(snapshot)}). Provider API skipped."
        )
        set_provider_status(self.provider_name, "cached", message, self._status_raw("sqlite_cache", snapshot))
        return {
            "status": "cached",
            "source": "sqlite_cache",
            "provider": self.provider_name,
            "category": category,
            "symbol": symbol.upper() if isinstance(symbol, str) else symbol,
            "message": message,
            "cache_fresh": True,
            "cache_age_minutes": snapshot.get("cache_age_minutes"),
            "collected_at": snapshot.get("cache_collected_at"),
            "cached_records": snapshot.get("rows", []),
        }

    def _stale_cache_result(
        self,
        category: str | None,
        symbol: str | None,
        message: str,
        status: str,
        limit: int = 120,
    ) -> dict[str, Any]:
        snapshot = cache_snapshot(self.provider_name, category, symbol, ttl_seconds=self._ttl_seconds(), limit=limit)
        has_cache = bool(snapshot.get("rows"))
        is_rate_limit = status == "rate_limited" or "rate limit" in str(message).lower() or "too many requests" in str(message).lower()
        fallback_statuses = {"rate_limited", "error", "auth_error", "method_not_allowed", "not_entitled"}
        fallback_active = has_cache and (status in fallback_statuses or is_rate_limit)
        if fallback_active and is_rate_limit:
            source = "sqlite_stale_cache_rate_limit_fallback"
        elif fallback_active:
            source = "sqlite_stale_cache_fallback"
        elif has_cache:
            source = "sqlite_stale_cache"
        else:
            source = "provider_error_no_cache"
        provider_status = "degraded" if fallback_active else ("rate_limited" if is_rate_limit else status)
        status_message = (
            f"{message}. Returning stale SQLite cache: {snapshot['count']} rows ({self._format_cache_age(snapshot)})."
            if has_cache
            else message
        )
        set_provider_status(
            self.provider_name,
            provider_status,
            status_message,
            self._status_raw(
                source,
                snapshot,
                rate_limit_fallback=bool(fallback_active and is_rate_limit),
                fallback_active=fallback_active,
                provider_error_status=status,
                provider_error_message=message,
                extra={"degraded_reason": status if fallback_active else None},
            ),
        )
        return {
            "status": "cached" if has_cache else status,
            "source": source,
            "provider": self.provider_name,
            "category": category,
            "symbol": symbol.upper() if isinstance(symbol, str) else symbol,
            "message": message,
            "cache_fresh": False,
            "fallback_active": fallback_active,
            "fallback_reason": status if fallback_active else None,
            "provider_error_status": status,
            "rate_limit_fallback": bool(fallback_active and is_rate_limit),
            "cache_age_minutes": snapshot.get("cache_age_minutes"),
            "collected_at": snapshot.get("cache_collected_at"),
            "cached_records": snapshot.get("rows", []),
        }
