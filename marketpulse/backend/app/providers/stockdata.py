from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record
from app.services.sentiment_service import score_text


class StockDataProvider(BaseCachedProvider):
    provider_name = "stockdata"

    def quote_and_news(self, ticker: str, force: bool = False) -> dict:
        cached = None if force else self._fresh_cache_result(None, ticker, limit=120, label=f"{ticker.upper()} stockdata quote/news")
        if cached:
            return cached
        if not is_configured(settings.stockdata_api_key):
            return self._stale_cache_result(None, ticker, "STOCKDATA_API_KEY not configured", "not_configured")

        quote_payload, quote_error, quote_status = request_json(
            self.provider_name,
            "GET",
            "https://api.stockdata.org/v1/data/quote",
            params={"symbols": ticker.upper(), "api_token": settings.stockdata_api_key},
        )
        news_payload, news_error, news_status = request_json(
            self.provider_name,
            "GET",
            "https://api.stockdata.org/v1/news/all",
            params={"symbols": ticker.upper(), "filter_entities": "true", "limit": 10, "api_token": settings.stockdata_api_key},
        )

        quote = None
        articles = []
        if quote_status == "ok" and quote_payload:
            item = (quote_payload.get("data") or [{}])[0]
            quote = item
            insert_record(
                self.provider_name,
                "quote",
                ticker,
                "instant",
                self._today().isoformat(),
                self._float(item.get("price")),
                self._float(item.get("volume")),
                None,
                f"{ticker.upper()} StockData quote",
                None,
                None,
                item,
            )
        if news_status == "ok" and news_payload:
            for article in news_payload.get("data") or []:
                text = f"{article.get('title', '')} {article.get('description', '')}"
                sentiment = score_text(text)
                day = (article.get("published_at") or "")[:10] or self._today().isoformat()
                record = {
                    "title": article.get("title"),
                    "summary": article.get("description"),
                    "url": article.get("url"),
                    "sentiment": sentiment,
                    "published_at": day,
                }
                insert_record(
                    self.provider_name,
                    "news",
                    ticker,
                    "daily",
                    day,
                    None,
                    None,
                    sentiment["sentiment_score"],
                    record["title"],
                    record["summary"],
                    record["url"],
                    article,
                )
                articles.append(record)

        if quote_status == "ok" or news_status == "ok":
            set_provider_status(
                self.provider_name,
                "ok",
                f"Stored quote={bool(quote)} news={len(articles)} from provider API",
                self._status_raw("provider_api", extra={"ticker": ticker, "stored_news": len(articles), "stored_quote": bool(quote)}),
            )
            return {"status": "ok", "provider": self.provider_name, "ticker": ticker.upper(), "quote": quote, "news": articles}

        return self._stale_cache_result(None, ticker, quote_error or news_error or "StockData failed", quote_status or news_status or "error")
