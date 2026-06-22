from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseCachedProvider, is_configured, request_json
from app.repositories.provider_status_repository import set_provider_status
from app.repositories.records_repository import insert_record, insert_topics
from app.services.sentiment_service import score_text
from app.services.topic_service import extract_lda_topics


class SerpstackProvider(BaseCachedProvider):
    provider_name = "serpstack"

    def search(self, query: str, ticker: str | None = None, force: bool = False) -> dict:
        cache_symbol = ticker or query
        cached = None if force else self._fresh_cache_result("search", cache_symbol, limit=60, label=f"{query} search results")
        if cached:
            return cached
        if not is_configured(settings.serpstack_api_key):
            return self._stale_cache_result("search", cache_symbol, "SERPSTACK_API_KEY not configured", "not_configured", limit=80)
        payload, error, status = request_json(
            self.provider_name,
            "GET",
            "http://api.serpstack.com/search",
            params={"access_key": settings.serpstack_api_key, "query": query, "num": 10},
        )
        if status != "ok" or not payload:
            return self._stale_cache_result("search", cache_symbol, error or "Serpstack failed", status, limit=80)
        results = []
        for item in payload.get("organic_results") or []:
            title = item.get("title") or "Search result"
            summary = item.get("snippet")
            sentiment = score_text(f"{title} {summary or ''}")
            day = self._today().isoformat()
            insert_record(
                self.provider_name,
                "search",
                cache_symbol,
                "daily",
                day,
                None,
                None,
                sentiment["sentiment_score"],
                title,
                summary,
                item.get("url"),
                item,
            )
            results.append({"title": title, "summary": summary, "url": item.get("url"), "sentiment": sentiment})
        topics = extract_lda_topics([f"{result['title']} {result.get('summary') or ''}" for result in results])
        insert_topics(self.provider_name, cache_symbol, topics)
        set_provider_status(
            self.provider_name,
            "ok",
            f"Stored {len(results)} search results from provider API",
            self._status_raw("provider_api", extra={"query": query, "stored_results": len(results)}),
        )
        return {"status": "ok", "provider": self.provider_name, "query": query, "results": results, "topics": topics}
