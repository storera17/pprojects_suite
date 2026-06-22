from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record


class FredProvider(BaseCachedProvider):
    provider_name = "fred"

    def series(self, series_id: str = "FEDFUNDS", force: bool = False) -> dict:
        cached = None if force else self._fresh_cache_result("macro", series_id, limit=500, label=f"FRED {series_id}")
        if cached:
            return cached
        if not is_configured(settings.fred_api_key):
            return self._stale_cache_result("macro", series_id, "FRED_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series_id, "api_key": settings.fred_api_key, "file_type": "json"},
        )
        if status != "ok" or not payload:
            return self._stale_cache_result("macro", series_id, error or "FRED failed", status)
        rows = []
        for observation in payload.get("observations") or []:
            value = self._float(observation.get("value"))
            if value is None:
                continue
            day = observation.get("date")
            insert_record(self.provider_name, "macro", series_id, "daily", day, value, None, None, f"FRED {series_id}", None, None, observation)
            rows.append({"date": day, "value": value, "series_id": series_id})
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(rows)} observations from provider API",
            self._status_raw("provider_api", extra={"series_id": series_id, "stored_rows": len(rows)}),
        )
        return {"status": "ok", "provider": self.provider_name, "series_id": series_id, "series": rows[-500:]}
