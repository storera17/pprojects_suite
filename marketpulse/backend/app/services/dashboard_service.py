from __future__ import annotations

from datetime import datetime

from app.repositories.provider_status_repository import get_provider_statuses
from app.repositories.records_repository import cache_snapshot, db_summary, get_topics, recent_records
from app.services.topic_service import clean_topics

TICKER_ALIASES = {
    "TSLA": ["tesla", "musk", "model y", "model 3", "cybertruck", "ev", "electric vehicle"],
    "AAPL": ["apple", "iphone", "ipad", "mac", "ios", "app store"],
    "MSFT": ["microsoft", "azure", "windows", "copilot", "openai"],
    "NVDA": ["nvidia", "gpu", "blackwell", "cuda", "semiconductor", "chips"],
    "AMZN": ["amazon", "aws", "prime", "bezos"],
    "META": ["meta", "facebook", "instagram", "whatsapp", "metaverse"],
    "GOOGL": ["google", "alphabet", "youtube", "gemini", "search"],
    "AMD": ["amd", "advanced micro devices", "radeon", "epyc", "ryzen"],
    "SPY": ["spy", "s&p", "sp 500", "s&p 500", "spdr", "index", "etf"],
    "QQQ": ["qqq", "nasdaq 100", "nasdaq-100", "invesco", "tech etf"],
}

FINANCE_TERMS = {
    "ai", "analyst", "bond", "bitcoin", "commodities", "crypto", "dollar", "dow", "downgrade", "earnings",
    "economy", "economic", "equity", "etf", "fed", "forex", "guidance", "inflation", "ipo", "market", "margin",
    "nasdaq", "oil", "profit", "rate", "revenue", "s&p", "sector", "semiconductor", "shares", "stock", "stocks",
    "target", "tech", "treasury", "upgrade", "yield",
}

WEAK_NEWS_TERMS = {"celebrity", "fashion", "gossip", "lifestyle", "recipe", "restaurant", "sports", "travel", "weekend"}


def period_to_days(period: str) -> int:
    return {"daily": 30, "weekly": 180, "monthly": 365, "yearly": 1825}.get((period or "daily").lower(), 30)


def bucket_for_period(day: str | None, period: str) -> str | None:
    if not day:
        return None
    try:
        dt = datetime.fromisoformat(day[:10]).date()
    except Exception:
        return day
    normalized = (period or "daily").lower()
    if normalized == "weekly":
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"
    if normalized == "monthly":
        return f"{dt.year}-{dt.month:02d}"
    if normalized == "yearly":
        return str(dt.year)
    return dt.isoformat()


def _text_for_row(row: dict) -> str:
    return " ".join(str(row.get(key) or "") for key in ("title", "summary", "symbol", "provider", "url")).strip()


def _is_probably_english(text: str) -> bool:
    if not text:
        return True
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return True
    ascii_letters = [char for char in letters if char.isascii()]
    return len(ascii_letters) / max(1, len(letters)) >= 0.82


def _ticker_aliases(ticker: str) -> list[str]:
    normalized = ticker.upper()
    return [normalized.lower(), *TICKER_ALIASES.get(normalized, [])]


def _market_relevance(row: dict, ticker: str | None = None) -> dict:
    symbol = (ticker or row.get("symbol") or "").upper()
    text_raw = _text_for_row(row)
    text = text_raw.lower()
    score = 0
    reasons: list[str] = []

    if symbol and (row.get("symbol") or "").upper() == symbol:
        score += 3
        reasons.append("stored_for_ticker")
    for alias in _ticker_aliases(symbol):
        if alias and alias in text:
            score += 3
            reasons.append(f"mentions_{alias[:18]}")
            break
    finance_hits = [term for term in FINANCE_TERMS if term in text]
    score += min(8, 2 * len(finance_hits))
    if finance_hits:
        reasons.append("finance_terms")
    weak_hits = [term for term in WEAK_NEWS_TERMS if term in text]
    score -= len(weak_hits) * 2
    if weak_hits:
        reasons.append("non_market_terms")
    english = _is_probably_english(text_raw)
    if not english:
        score -= 5
        reasons.append("non_english")
    if row.get("category") == "search":
        score += 1
    label = "high" if score >= 7 else "medium" if score >= 3 else "low"
    return {
        **row,
        "market_relevance_score": score,
        "market_relevance": label,
        "ticker_relevant": label in {"high", "medium"} and english,
        "is_english": english,
        "relevance_reasons": reasons,
    }


def _ticker_provider_health(ticker: str, ttl_seconds: int) -> list[dict]:
    ticker = ticker.upper()
    specs = [
        ("polygon", "price", ticker, "Price history"),
        ("alpha_vantage", "price", ticker, "Price history"),
        ("finnhub", "quote", ticker, "Realtime quote"),
        ("stockdata", None, ticker, "Quote/news"),
        ("marketaux", "news", ticker, "Ticker news"),
        ("nytimes", "news", ticker, "Ticker news"),
        ("serpstack", "search", ticker, "Search news"),
        ("fred", "macro", None, "Macro context"),
        ("coinlayer", "crypto", None, "Crypto context"),
        ("alchemy", "crypto", None, "Crypto token context"),
        ("currencylayer", "fx", None, "FX context"),
    ]
    global_status = {row.get("provider"): row for row in get_provider_statuses()}
    rows = []
    for provider, category, symbol, label in specs:
        snapshot = cache_snapshot(provider, category, symbol, ttl_seconds=ttl_seconds, limit=250)
        global_row = global_status.get(provider, {})
        if snapshot.get("fresh"):
            status = "fresh_cache"
            message = f"{label}: {snapshot['count']} cached rows are fresh; provider call can be skipped."
        elif snapshot.get("rows"):
            status = "stale_cache"
            message = f"{label}: {snapshot['count']} cached rows exist but are outside the TTL. Refresh when rate limits allow."
        elif global_row.get("status") in {"auth_error", "degraded", "error", "method_not_allowed", "not_configured", "not_entitled", "rate_limited"}:
            status = global_row.get("status")
            message = global_row.get("message") or f"{label}: no ticker-specific cache is stored yet."
        else:
            status = "missing"
            message = f"{label}: no ticker-specific cache is stored yet."
        rows.append(
            {
                "provider": provider,
                "category": category or "mixed",
                "symbol": symbol,
                "status": status,
                "message": message,
                "source": "sqlite_cache" if snapshot.get("rows") else "not_available",
                "cache_source": "sqlite_cache" if snapshot.get("rows") else "not_available",
                "cache_record_count": snapshot.get("count"),
                "cache_age_minutes": snapshot.get("cache_age_minutes"),
                "cache_age_seconds": snapshot.get("cache_age_seconds"),
                "cache_collected_at": snapshot.get("cache_collected_at"),
                "cache_fresh": bool(snapshot.get("fresh")),
                "fallback_active": bool(global_row.get("fallback_active")),
                "fallback_reason": global_row.get("fallback_reason") or global_row.get("provider_error_status"),
                "rate_limit_fallback": bool(global_row.get("rate_limit_fallback")),
                "provider_error_status": global_row.get("provider_error_status"),
                "last_attempt_at": global_row.get("last_attempt_at"),
                "last_success_at": global_row.get("last_success_at"),
            }
        )
    return rows


def _readiness(summary: dict, volume_points: int, relevant_news_count: int, providers: list[dict]) -> dict:
    price_available = bool((summary.get("price_points") or 0) > 0 or summary.get("latest_price") is not None or summary.get("latest_quote") is not None)
    quote_available = bool(summary.get("latest_quote") is not None)
    news_available = relevant_news_count > 0
    sentiment_available = bool((summary.get("sentiment_items") or 0) > 0)
    volume_available = volume_points > 0
    provider_fresh = sum(1 for provider in providers if provider.get("cache_fresh"))

    score = 0
    score += 30 if price_available else 0
    score += 15 if quote_available else 0
    score += 15 if volume_available else 0
    score += 20 if news_available else 0
    score += 10 if sentiment_available else 0
    score += min(10, provider_fresh)

    missing = []
    if not price_available:
        missing.append("price_or_quote")
    if not volume_available:
        missing.append("volume")
    if not news_available:
        missing.append("ticker_relevant_news")
    if not sentiment_available:
        missing.append("sentiment")

    if score >= 80:
        status = "complete"
    elif price_available and score >= 55:
        status = "analysis_ready_partial"
    elif price_available:
        status = "price_only"
    else:
        status = "not_ready"

    return {
        "status": status,
        "coverage_score": score,
        "valid_for_workspace": price_available,
        "price_available": price_available,
        "quote_available": quote_available,
        "volume_available": volume_available,
        "news_available": news_available,
        "sentiment_available": sentiment_available,
        "provider_fresh_count": provider_fresh,
        "missing": missing,
        "message": "Ready for analysis." if status == "complete" else "Partial coverage; unavailable sections are shown honestly instead of breaking the page.",
    }


def _series_from_price_rows(rows: list[dict], period: str = "daily", limit: int = 500) -> list[dict]:
    series: dict[str, dict] = {}
    for row in reversed(rows):
        bucket = bucket_for_period(row.get("event_date"), period)
        if not bucket:
            continue
        series[bucket] = {
            "date": bucket,
            "close": row.get("value_primary"),
            "volume": row.get("value_secondary"),
            "provider": row.get("provider"),
        }
    return list(series.values())[-limit:]


def _daily_change_from_rows(rows: list[dict]) -> dict:
    points = _series_from_price_rows(rows, "daily", limit=10)
    valid = [point for point in points if point.get("close") is not None]
    if len(valid) < 2:
        return {"available": False, "message": "Need at least two stored daily price rows to calculate daily change."}
    latest = valid[-1]
    previous = valid[-2]
    latest_close = float(latest.get("close"))
    previous_close = float(previous.get("close"))
    if previous_close == 0:
        return {"available": False, "message": "Stored daily price rows are incomplete."}
    change = latest_close - previous_close
    change_pct = (change / previous_close) * 100
    return {
        "available": True,
        "latest_date": latest.get("date"),
        "previous_date": previous.get("date"),
        "latest_close": round(latest_close, 4),
        "previous_close": round(previous_close, 4),
        "change": round(change, 4),
        "change_percent": round(change_pct, 4),
        "direction": "up" if change > 0 else ("down" if change < 0 else "flat"),
        "provider": latest.get("provider") or previous.get("provider"),
    }


def _price_periods_for_ticker(ticker: str) -> dict[str, list[dict]]:
    rows = recent_records(category="price", symbol=ticker, days=1825, limit=5000)
    return {
        "day": _series_from_price_rows(rows, "daily", limit=90),
        "week": _series_from_price_rows(rows, "weekly", limit=156),
        "month": _series_from_price_rows(rows, "monthly", limit=84),
        "year": _series_from_price_rows(rows, "yearly", limit=10),
    }


def build_dashboard(ticker: str, period: str = "daily", ttl_seconds: int = 86400) -> dict:
    symbol = ticker.upper()
    days = period_to_days(period)
    price_rows = recent_records(category="price", symbol=symbol, days=days, limit=2000)
    quote_rows = recent_records(category="quote", symbol=symbol, days=days, limit=200)
    news_rows = recent_records(category="news", symbol=symbol, days=days, limit=500)
    search_rows = recent_records(category="search", symbol=symbol, days=days, limit=300)
    macro_rows = recent_records(category="macro", symbol=None, days=days, limit=1000)
    crypto_rows = recent_records(category="crypto", symbol=None, days=days, limit=500)
    fx_rows = recent_records(category="fx", symbol=None, days=days, limit=500)
    providers = _ticker_provider_health(symbol, ttl_seconds)

    price_by_provider: dict[str, list[dict]] = {}
    volume_by_provider: dict[str, list[dict]] = {}
    for row in reversed(price_rows):
        provider = row["provider"]
        item = {
            "date": bucket_for_period(row["event_date"], period),
            "close": row["value_primary"],
            "volume": row["value_secondary"],
            "provider": provider,
        }
        price_by_provider.setdefault(provider, []).append(item)
        if item["volume"] is not None:
            volume_by_provider.setdefault(provider, []).append({"date": item["date"], "value": item["volume"], "provider": provider})

    for provider, rows in list(price_by_provider.items()):
        deduped = {}
        for row in rows:
            if row["date"]:
                deduped[row["date"]] = row
        price_by_provider[provider] = list(deduped.values())
    for provider, rows in list(volume_by_provider.items()):
        deduped = {}
        for row in rows:
            if row["date"]:
                deduped[row["date"]] = row
        volume_by_provider[provider] = list(deduped.values())

    if not any(volume_by_provider.values()):
        quote_volume = []
        for row in reversed(quote_rows):
            if row.get("value_secondary") is not None:
                quote_volume.append({"date": bucket_for_period(row.get("event_date"), period), "value": row.get("value_secondary"), "provider": row.get("provider")})
        if quote_volume:
            volume_by_provider["quote_volume"] = quote_volume

    raw_news = sorted(news_rows + search_rows, key=lambda row: row.get("event_date") or row.get("created_at") or "", reverse=True)
    enriched_news = [_market_relevance(row, symbol) for row in raw_news]
    relevant_news = [row for row in enriched_news if row.get("ticker_relevant")]
    display_news = sorted(
        relevant_news or enriched_news,
        key=lambda row: (row.get("market_relevance_score") or 0, row.get("event_date") or row.get("created_at") or ""),
        reverse=True,
    )[:18]
    high_relevance_news = [row for row in display_news if row.get("market_relevance") == "high"]

    sentiment_by_date: dict[str, dict] = {}
    for row in relevant_news:
        bucket = bucket_for_period(row.get("event_date"), period)
        if not bucket:
            continue
        item = sentiment_by_date.setdefault(bucket, {"date": bucket, "scores": [], "count": 0})
        if row.get("sentiment_score") is not None:
            item["scores"].append(float(row["sentiment_score"]))
        item["count"] += 1
    sentiment_series = [
        {"date": key, "sentiment": round(sum(value["scores"]) / len(value["scores"]), 4) if value["scores"] else 0.0, "count": value["count"]}
        for key, value in sorted(sentiment_by_date.items())
    ]

    macro_by_series: dict[str, list[dict]] = {}
    for row in reversed(macro_rows):
        macro_by_series.setdefault(row.get("symbol") or "macro", []).append({"date": bucket_for_period(row["event_date"], period), "value": row["value_primary"], "provider": row.get("provider")})
    crypto_by_symbol: dict[str, list[dict]] = {}
    for row in reversed(crypto_rows):
        crypto_by_symbol.setdefault(row.get("symbol") or row.get("title") or "crypto", []).append({"date": bucket_for_period(row["event_date"], period), "value": row["value_primary"], "provider": row.get("provider"), "title": row.get("title")})
    fx_by_symbol: dict[str, list[dict]] = {}
    for row in reversed(fx_rows):
        fx_by_symbol.setdefault(row.get("symbol") or row.get("title") or "fx", []).append({"date": bucket_for_period(row["event_date"], period), "value": row["value_primary"], "provider": row.get("provider"), "title": row.get("title")})

    latest_quote = quote_rows[0] if quote_rows else None
    latest_price = price_rows[0] if price_rows else None
    price_periods = _price_periods_for_ticker(symbol)
    daily_change = _daily_change_from_rows(recent_records(category="price", symbol=symbol, days=14, limit=50))
    sentiment_timeline = [
        {
            "date": item.get("date"),
            "label": "positive" if (item.get("sentiment") or 0) >= 0.08 else ("negative" if (item.get("sentiment") or 0) <= -0.08 else "neutral"),
            "sentiment": item.get("sentiment"),
            "count": item.get("count", 0),
        }
        for item in sentiment_series
    ]
    sentiment_avg = round(sum(item["sentiment"] for item in sentiment_series) / len(sentiment_series), 4) if sentiment_series else None
    sentiment_count = sum(int(item.get("count") or 0) for item in sentiment_series)
    provider_attempts = [provider.get("last_attempt_at") or provider.get("cache_collected_at") for provider in providers if provider.get("last_attempt_at") or provider.get("cache_collected_at")]
    last_refreshed_at = max(provider_attempts) if provider_attempts else None
    api_skipped_count = sum(1 for provider in providers if provider.get("cache_fresh"))
    degraded_fallbacks = sum(1 for provider in providers if provider.get("fallback_active"))
    rate_limit_fallbacks = sum(1 for provider in providers if provider.get("rate_limit_fallback"))
    cache_ages = [provider.get("cache_age_minutes") for provider in providers if isinstance(provider.get("cache_age_minutes"), (int, float))]
    freshest_cache_age_minutes = min(cache_ages) if cache_ages else None
    volume_points = sum(len(values) for values in volume_by_provider.values())

    if sentiment_avg is None:
        sentiment_label = "insufficient data"
    elif sentiment_avg >= 0.08:
        sentiment_label = "positive"
    elif sentiment_avg <= -0.08:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"

    summary = {
        "latest_price": latest_price["value_primary"] if latest_price else None,
        "latest_price_provider": latest_price["provider"] if latest_price else None,
        "latest_quote": latest_quote["value_primary"] if latest_quote else None,
        "latest_quote_provider": latest_quote["provider"] if latest_quote else None,
        "news_count": len(news_rows) + len(search_rows),
        "ticker_relevant_news_count": len(relevant_news),
        "high_relevance_news_count": len(high_relevance_news),
        "price_points": len(price_rows),
        "volume_points": volume_points,
        "macro_points": len(macro_rows),
        "crypto_points": len(crypto_rows),
        "fx_points": len(fx_rows),
        "sentiment_avg": sentiment_avg,
        "sentiment_items": sentiment_count,
        "sentiment_label": sentiment_label,
        "last_refreshed_at": last_refreshed_at,
        "api_skipped_count": api_skipped_count,
        "degraded_fallback_count": degraded_fallbacks,
        "rate_limit_fallback_count": rate_limit_fallbacks,
        "freshest_cache_age_minutes": freshest_cache_age_minutes,
        "daily_change": daily_change,
    }
    readiness = _readiness(summary, volume_points, len(relevant_news), providers)

    if latest_price:
        price_takeaway = f"{symbol} has {len(price_rows)} stored price rows with latest price context from {latest_price['provider']}."
    elif latest_quote:
        price_takeaway = f"{symbol} has quote coverage but no stored daily price bars yet."
    else:
        price_takeaway = f"{symbol} has no stored price or quote rows yet. Run Refresh {symbol} to test provider coverage."
    news_takeaway = f"{len(relevant_news)} ticker-relevant market items are available from {len(news_rows) + len(search_rows)} stored news/search rows."
    quality_takeaway = f"Readiness is {readiness['status']} with a {readiness['coverage_score']}/100 coverage score. Missing: {', '.join(readiness['missing']) or 'none'}."
    cache_takeaway = f"{api_skipped_count} data categories can use fresh SQLite cache; {degraded_fallbacks} provider(s) are currently serving degraded cached data."
    summary["executive_takeaway"] = " ".join([price_takeaway, news_takeaway, quality_takeaway, cache_takeaway])

    return {
        "status": "ok",
        "ticker": symbol,
        "period": period,
        "source": "local_sqlite_api_agents",
        "summary": summary,
        "quality": readiness,
        "price_history": price_by_provider,
        "price_periods": price_periods,
        "daily_change": daily_change,
        "volume_history": volume_by_provider,
        "sentiment_series": sentiment_series,
        "sentiment_timeline": sentiment_timeline,
        "macro_series": macro_by_series,
        "news": display_news,
        "topics": clean_topics(get_topics(symbol, 40), 20),
        "crypto": crypto_rows[:80],
        "fx": fx_rows[:80],
        "crypto_series": crypto_by_symbol,
        "fx_series": fx_by_symbol,
        "provider_statuses": providers,
        "db_summary": db_summary(),
    }
