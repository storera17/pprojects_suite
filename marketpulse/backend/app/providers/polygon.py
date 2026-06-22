from __future__ import annotations

from datetime import timedelta

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record


class PolygonProvider(BaseCachedProvider):
    provider_name = "polygon"

    def history(self, ticker: str, days: int = 365, force: bool = False) -> dict:
        cached = None if force else self._fresh_cache_result("price", ticker, limit=max(days, 365), label=f"{ticker.upper()} price history")
        if cached:
            return cached
        if not is_configured(settings.polygon_api_key):
            return self._stale_cache_result("price", ticker, "POLYGON_API_KEY not configured", "not_configured")
        end = self._today()
        start = end - timedelta(days=max(days * 2, 30))
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker.upper()}/range/1/day/{start}/{end}"
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            url,
            params={"adjusted": "true", "sort": "asc", "limit": 5000, "apiKey": settings.polygon_api_key},
        )
        if status != "ok" or not payload:
            return self._stale_cache_result("price", ticker, error or "Polygon request failed", status)
        rows = []
        for item in (payload.get("results") or [])[-days:]:
            day = self._iso_day_from_ms(item.get("t"))
            close = self._float(item.get("c"))
            if not day or close is None:
                continue
            record = {
                "date": day,
                "open": self._float(item.get("o")),
                "high": self._float(item.get("h")),
                "low": self._float(item.get("l")),
                "close": close,
                "volume": self._float(item.get("v")),
            }
            insert_record(
                self.provider_name,
                "price",
                ticker,
                "daily",
                day,
                close,
                record.get("volume"),
                None,
                f"{ticker.upper()} Polygon close",
                None,
                None,
                record,
            )
            rows.append(record)
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(rows)} price bars from provider API",
            self._status_raw("provider_api", extra={"ticker": ticker, "stored_rows": len(rows)}),
        )
        return {"status": "ok", "provider": self.provider_name, "ticker": ticker.upper(), "series": rows}
