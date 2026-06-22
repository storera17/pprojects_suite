from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record


class FinnhubProvider(BaseCachedProvider):
    provider_name = "finnhub"

    def quote(self, ticker: str, force: bool = False) -> dict:
        cached = None if force else self._fresh_cache_result("quote", ticker, limit=5, label=f"{ticker.upper()} quote")
        if cached:
            return cached
        if not is_configured(settings.finnhub_api_key):
            return self._stale_cache_result("quote", ticker, "FINNHUB_API_KEY not configured", "not_configured", limit=1)
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "https://finnhub.io/api/v1/quote",
            params={"symbol": ticker.upper(), "token": settings.finnhub_api_key},
        )
        if status != "ok" or not payload:
            return self._stale_cache_result("quote", ticker, error or "Finnhub request failed", status, limit=1)
        price = self._float(payload.get("c"))
        day = self._today().isoformat()
        insert_record(
            self.provider_name,
            "quote",
            ticker,
            "instant",
            day,
            price,
            self._float(payload.get("dp")),
            None,
            f"{ticker.upper()} Finnhub quote",
            None,
            None,
            payload,
        )
        set_provider_status(self.provider_name, "ok", "Stored quote from provider API", self._status_raw("provider_api", extra={"ticker": ticker}))
        return {"status": "ok", "provider": self.provider_name, "ticker": ticker.upper(), "quote": payload}
