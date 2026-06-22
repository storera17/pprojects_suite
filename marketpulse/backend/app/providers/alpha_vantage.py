from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, classify_provider_error, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record


class AlphaVantageProvider(BaseCachedProvider):
    provider_name = "alpha_vantage"

    def history(self, ticker: str, days: int = 100, force: bool = False) -> dict:
        cached = None if force else self._fresh_cache_result("price", ticker, limit=max(days, 100), label=f"{ticker.upper()} price history")
        if cached:
            return cached
        if not is_configured(settings.alpha_vantage_api_key):
            return self._stale_cache_result("price", ticker, "ALPHA_VANTAGE_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "https://www.alphavantage.co/query",
            params={"function": "TIME_SERIES_DAILY", "symbol": ticker.upper(), "outputsize": "compact", "apikey": settings.alpha_vantage_api_key},
        )
        if status != "ok" or not payload or "Time Series (Daily)" not in payload:
            message = error or (payload.get("Note") if isinstance(payload, dict) else "Alpha Vantage request failed")
            return self._stale_cache_result("price", ticker, str(message), classify_provider_error(str(message)))
        rows = []
        for day in sorted(payload.get("Time Series (Daily)", {}).keys())[-days:]:
            item = payload["Time Series (Daily)"][day]
            close = self._float(item.get("4. close"))
            if close is None:
                continue
            record = {
                "date": day,
                "open": self._float(item.get("1. open")),
                "high": self._float(item.get("2. high")),
                "low": self._float(item.get("3. low")),
                "close": close,
                "volume": self._float(item.get("5. volume")),
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
                f"{ticker.upper()} Alpha Vantage close",
                None,
                None,
                record,
            )
            rows.append(record)
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(rows)} daily bars from provider API",
            self._status_raw("provider_api", extra={"ticker": ticker, "stored_rows": len(rows)}),
        )
        return {"status": "ok", "provider": self.provider_name, "ticker": ticker.upper(), "series": rows}
