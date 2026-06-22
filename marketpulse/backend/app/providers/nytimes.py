from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record, insert_topics, recent_records
from app.services.sentiment_service import score_text
from app.services.topic_service import extract_lda_topics


class NYTimesProvider(BaseCachedProvider):
    provider_name = "nytimes"

    def news(self, ticker: str, force: bool = False) -> dict:
        cached = None if force else self._fresh_cache_result("news", ticker, limit=60, label=f"{ticker.upper()} NYTimes news")
        if cached:
            return cached
        if not is_configured(settings.nytimes_api_key):
            return self._stale_cache_result("news", ticker, "NYTIMES_API_KEY not configured", "not_configured")
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "https://api.nytimes.com/svc/search/v2/articlesearch.json",
            params={"q": ticker.upper(), "sort": "newest", "api-key": settings.nytimes_api_key},
        )
        if status != "ok" or not payload:
            return self._stale_cache_result("news", ticker, error or "NYTimes failed", status)
        docs = payload.get("response", {}).get("docs", [])[:10]
        articles = []
        for doc in docs:
            title = doc.get("headline", {}).get("main") or doc.get("abstract") or "NYTimes article"
            summary = doc.get("abstract") or doc.get("snippet")
            sentiment = score_text(f"{title} {summary or ''}")
            day = (doc.get("pub_date") or "")[:10] or self._today().isoformat()
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
                doc.get("web_url"),
                doc,
            )
            articles.append({"title": title, "summary": summary, "url": doc.get("web_url"), "published_at": day, "sentiment": sentiment})
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
