from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record, insert_topics, recent_records
from app.services.sentiment_service import score_text
from app.services.topic_service import extract_lda_topics


class MarketauxProvider(BaseCachedProvider):
    provider_name = "marketaux"

    def news(self, ticker: str, force: bool = False) -> dict:
        cached = None if force else self._fresh_cache_result("news", ticker, limit=80, label=f"{ticker.upper()} Marketaux news")
        if cached:
            return cached
        if not is_configured(settings.marketaux_api_key):
            return self._stale_cache_result("news", ticker, "MARKETAUX_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "https://api.marketaux.com/v1/news/all",
            params={"symbols": ticker.upper(), "filter_entities": "true", "language": "en", "api_token": settings.marketaux_api_key},
        )
        if status != "ok" or not payload:
            return self._stale_cache_result("news", ticker, error or "Marketaux failed", status)
        articles = []
        for article in (payload.get("data") or [])[:20]:
            title = article.get("title") or "Marketaux article"
            summary = article.get("description") or article.get("snippet")
            sentiment = score_text(f"{title} {summary or ''}")
            day = (article.get("published_at") or "")[:10] or self._today().isoformat()
            insert_record(
                self.provider_name,
                "news",
                ticker,
                "daily",
                day,
                None,
                None,
                sentiment["sentiment_score"],
                title,
                summary,
                article.get("url"),
                article,
            )
            articles.append({"title": title, "summary": summary, "url": article.get("url"), "published_at": day, "sentiment": sentiment})
        self._store_topics(ticker)
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(articles)} articles from provider API",
            self._status_raw("provider_api", extra={"ticker": ticker, "stored_articles": len(articles)}),
        )
        return {"status": "ok", "provider": self.provider_name, "ticker": ticker.upper(), "articles": articles}

    def _store_topics(self, ticker: str) -> list[dict]:
        rows = recent_records(provider=self.provider_name, category="news", symbol=ticker, days=180, limit=100)
        texts = [f"{row.get('title') or ''} {row.get('summary') or ''}" for row in rows]
        topics = extract_lda_topics(texts)
        insert_topics(self.provider_name, ticker, topics)
        return topics
