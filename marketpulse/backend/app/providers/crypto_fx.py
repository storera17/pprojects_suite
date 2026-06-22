from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record


class CryptoFxProvider(BaseCachedProvider):
    provider_name = ""

    def coinlayer(self, force: bool = False) -> dict:
        self.provider_name = "coinlayer"
        cached = None if force else self._fresh_cache_result("crypto", None, limit=50, label="Coinlayer crypto rates")
        if cached:
            return cached
        if not is_configured(settings.coinlayer_api_key):
            return self._stale_cache_result("crypto", None, "COINLAYER_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "http://api.coinlayer.com/live",
            params={"access_key": settings.coinlayer_api_key, "symbols": "BTC,ETH,SOL,DOGE,ADA,AVAX,LINK"},
        )
        if status != "ok" or not payload or not payload.get("success", True):
            return self._stale_cache_result("crypto", None, error or str(payload.get("error") if payload else "Coinlayer failed"), status)
        day = self._today().isoformat()
        rates = payload.get("rates") or {}
        for symbol, price in rates.items():
            insert_record(self.provider_name, "crypto", symbol, "daily", day, self._float(price), None, None, f"{symbol} Coinlayer USD", None, None, {"symbol": symbol, "price": price})
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(rates)} crypto rates from provider API",
            self._status_raw("provider_api", extra={"stored_rates": len(rates)}),
        )
        return {"status": "ok", "provider": self.provider_name, "rates": rates}

    def alchemy(self, force: bool = False) -> dict:
        self.provider_name = "alchemy"
        cached = None if force else self._fresh_cache_result("crypto", None, limit=50, label="Alchemy crypto prices")
        if cached:
            return cached
        if not is_configured(settings.alchemy_api_key):
            return self._stale_cache_result("crypto", None, "ALCHEMY_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            f"https://api.g.alchemy.com/prices/v1/{settings.alchemy_api_key}/tokens/by-symbol",
            params=[("symbols", symbol) for symbol in ["BTC", "ETH", "SOL", "DOGE", "ADA", "AVAX", "LINK"]],
            headers={"accept": "application/json"},
        )
        if status != "ok" or not payload:
            return self._stale_cache_result("crypto", None, error or "Alchemy failed", status)
        day = self._today().isoformat()
        items = payload.get("data", payload if isinstance(payload, list) else [])
        tokens = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            symbol = item.get("symbol")
            prices = item.get("prices") or []
            price = self._float(prices[0].get("value")) if prices else None
            if symbol:
                insert_record(self.provider_name, "crypto", symbol, "daily", day, price, None, None, f"{symbol} Alchemy USD", None, None, item)
                tokens.append({"symbol": symbol, "price_usd": price})
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(tokens)} token prices from provider API",
            self._status_raw("provider_api", extra={"stored_tokens": len(tokens)}),
        )
        return {"status": "ok", "provider": self.provider_name, "tokens": tokens}

    def currencylayer(self, force: bool = False) -> dict:
        self.provider_name = "currencylayer"
        cached = None if force else self._fresh_cache_result("fx", None, limit=50, label="Currencylayer FX rates")
        if cached:
            return cached
        if not is_configured(settings.currencylayer_api_key):
            return self._stale_cache_result("fx", None, "CURRENCYLAYER_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "http://api.currencylayer.com/live",
            params={"access_key": settings.currencylayer_api_key, "currencies": "EUR,GBP,JPY,CAD,CHF,AUD,CNY,INR"},
        )
        if status != "ok" or not payload or not payload.get("success", True):
            return self._stale_cache_result("fx", None, error or str(payload.get("error") if payload else "Currencylayer failed"), status)
        quotes = payload.get("quotes") or {}
        day = self._today().isoformat()
        rates: dict[str, float | str] = {}
        for pair, value in quotes.items():
            currency = pair.replace("USD", "")
            rates[currency] = value
            insert_record(self.provider_name, "fx", currency, "daily", day, self._float(value), None, None, f"USD/{currency}", None, None, {"pair": pair, "rate": value})
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(rates)} FX rates from provider API",
            self._status_raw("provider_api", extra={"stored_rates": len(rates)}),
        )
        return {"status": "ok", "provider": self.provider_name, "base": "USD", "rates": rates}

    def fixer(self, force: bool = False) -> dict:
        self.provider_name = "fixer"
        cached = None if force else self._fresh_cache_result("fx", None, limit=50, label="Fixer FX rates")
        if cached:
            return cached
        if not is_configured(settings.fixer_api_key):
            return self._stale_cache_result("fx", None, "FIXER_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "https://data.fixer.io/api/latest",
            params={"access_key": settings.fixer_api_key, "symbols": "USD,EUR,GBP,JPY,CAD,CHF,AUD,CNY,INR"},
        )
        if status != "ok" or not payload or not payload.get("success", True):
            return self._stale_cache_result("fx", None, error or str(payload.get("error") if payload else "Fixer failed"), status)
        rates = payload.get("rates") or {}
        base = payload.get("base") or "EUR"
        day = payload.get("date") or self._today().isoformat()
        stored = {}
        for currency, value in rates.items():
            if currency == base:
                continue
            stored[currency] = value
            insert_record(self.provider_name, "fx", currency, "daily", day, self._float(value), None, None, f"{base}/{currency}", None, None, {"base": base, "currency": currency, "rate": value})
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(stored)} FX rates from provider API",
            self._status_raw("provider_api", extra={"stored_rates": len(stored), "base": base}),
        )
        return {"status": "ok", "provider": self.provider_name, "base": base, "rates": stored}
