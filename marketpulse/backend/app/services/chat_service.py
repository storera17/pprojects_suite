from __future__ import annotations

import re

from app.core.config import settings
from app.services.dashboard_service import build_dashboard


def _chat_intent(message: str) -> str:
    text = (message or "").lower().strip()
    if not text or re.fullmatch(r"(hi|hello|hey|yo|good morning|good afternoon|good evening)[!. ]*", text):
        return "greeting"
    if any(word in text for word in ["provider", "cache", "fresh", "stale", "rate limit", "ratelimit", "fallback"]):
        return "provider_health"
    if any(word in text for word in ["sentiment", "mood", "tone"]):
        return "sentiment"
    if any(word in text for word in ["news", "headline", "article"]):
        return "news"
    if any(word in text for word in ["volume", "price", "trend", "chart"]):
        return "price"
    if any(word in text for word in ["crypto", "fx", "forex", "currency", "macro", "rates"]):
        return "context"
    if any(word in text for word in ["risk", "gap", "missing", "quality", "ready", "custom", "add"]):
        return "quality"
    return "summary"


def local_chat_answer(message: str, ticker: str = "SPY", period: str = "daily") -> dict:
    dashboard = build_dashboard(ticker, period)
    summary = dashboard["summary"]
    quality = dashboard.get("quality", {})
    topics = dashboard.get("topics", [])[:5]
    news = [item for item in dashboard.get("news", []) if item.get("ticker_relevant")][:5]
    providers = dashboard.get("provider_statuses", [])
    intent = _chat_intent(message)
    symbol = ticker.upper()

    if intent == "greeting":
        answer = (
            f"Hi - I am ready to analyze {symbol}. I can summarize the ticker, explain provider/cache health, "
            "check sentiment, review news relevance, identify missing data, or describe whether this ticker is ready for a custom workspace."
        )
    elif intent == "provider_health":
        lines = [f"Provider and cache health for {symbol}:"]
        for provider in providers[:12]:
            lines.append(
                f"- {provider.get('provider')} / {provider.get('category')}: {provider.get('status')} "
                f"| rows={provider.get('cache_record_count')} "
                f"| age={provider.get('cache_age_minutes')} min "
                f"| fallback={bool(provider.get('rate_limit_fallback'))}"
            )
        answer = "\n".join(lines)
    elif intent == "sentiment":
        if summary.get("sentiment_items"):
            answer = f"{symbol} sentiment is {summary.get('sentiment_label')} ({summary.get('sentiment_avg')}) across {summary.get('sentiment_items')} ticker-relevant English news/search rows."
        else:
            answer = f"I do not have enough ticker-relevant English news text to score {symbol} sentiment yet. Refresh news providers or try broader market context."
    elif intent == "news":
        if news:
            answer = "Ticker-relevant headlines:\n" + "\n".join([f"- [{item.get('market_relevance')}] {item.get('title')}" for item in news])
        else:
            answer = f"No high/medium relevance English headlines are stored for {symbol} yet. The dashboard will avoid using unrelated or non-English articles for sentiment."
    elif intent == "price":
        volume_message = f"Volume rows available: {summary.get('volume_points', 0)}." if summary.get("volume_points") else "Volume history is not available from the current stored providers."
        answer = f"{symbol} has {summary.get('price_points')} stored price rows. Latest stored price is {summary.get('latest_price')} from {summary.get('latest_price_provider') or 'no provider'}. {volume_message}"
    elif intent == "context":
        answer = f"Broader context available in SQLite: {summary.get('macro_points')} macro rows, {summary.get('crypto_points')} crypto rows, and {summary.get('fx_points')} FX rows. These are market context rows, not {symbol}-specific fundamentals."
    elif intent == "quality":
        answer = f"{symbol} readiness: {quality.get('status')} with coverage score {quality.get('coverage_score')}/100. Valid workspace: {quality.get('valid_for_workspace')}. Missing: {', '.join(quality.get('missing') or []) or 'none'}."
    else:
        topic_text = "; ".join([topic.get("label") or ", ".join(topic.get("keywords", [])[:4]) for topic in topics]) or "no clean topics yet"
        headline_text = " | ".join([str(item.get("title") or "Untitled")[:90] for item in news]) or "no ticker-relevant headlines yet"
        answer = (
            f"MarketPulse summary for {symbol} ({period}).\n\n"
            f"Latest stored price: {summary.get('latest_price')} from {summary.get('latest_price_provider') or 'no stored provider yet'}.\n"
            f"Ticker-specific coverage: {summary.get('price_points')} price rows, {summary.get('volume_points')} volume rows, {summary.get('ticker_relevant_news_count')} relevant news/search rows, and {summary.get('sentiment_items')} sentiment-scored rows.\n"
            f"Broader context available: {summary.get('macro_points')} macro rows, {summary.get('crypto_points')} crypto rows, {summary.get('fx_points')} FX rows.\n"
            f"Readiness: {quality.get('status')} ({quality.get('coverage_score')}/100).\n"
            f"Clean topic clusters: {topic_text}.\n"
            f"Relevant headlines: {headline_text}."
        )
    return {"status": "ok", "mode": settings.llm_mode, "intent": intent, "answer": answer, "dashboard": dashboard}
