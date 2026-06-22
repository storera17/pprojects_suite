from __future__ import annotations

from fastapi import APIRouter, Query

from app.repositories.records_repository import recent_records
from app.repositories.watchlist_repository import add_watchlist_ticker, get_watchlist_tickers
from app.schemas.tickers import CustomTickerRequest
from app.services.dashboard_service import build_dashboard
from app.services.refresh_service import RefreshOrchestrator

router = APIRouter(tags=["tickers"])


@router.get("/tickers/watchlist")
def ticker_watchlist():
    tickers = get_watchlist_tickers()
    return {"status": "ok", "tickers": tickers, "default_count": len(tickers)}


@router.get("/tickers/{ticker}/availability")
def ticker_availability(ticker: str):
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return {"status": "error", "ticker": symbol, "message": "Ticker is required."}

    rows = recent_records(symbol=symbol, days=3650, limit=5000)
    by_category: dict[str, int] = {}
    by_provider: dict[str, int] = {}
    latest_event = None
    latest_created = None
    for row in rows:
        category = row.get("category") or "unknown"
        provider = row.get("provider") or "unknown"
        by_category[category] = by_category.get(category, 0) + 1
        by_provider[provider] = by_provider.get(provider, 0) + 1
        latest_event = max(latest_event or "", row.get("event_date") or "")
        latest_created = max(latest_created or "", row.get("created_at") or "")
    return {
        "status": "ok",
        "ticker": symbol,
        "has_data": bool(rows),
        "record_count": len(rows),
        "latest_event_date": latest_event,
        "latest_created_at": latest_created,
        "categories": by_category,
        "providers": by_provider,
        "message": f"Stored data is available for {symbol}." if rows else f"No stored data exists for {symbol} yet.",
    }


@router.get("/tickers/{ticker}/records")
def ticker_records(
    ticker: str,
    category: str | None = None,
    provider: str | None = None,
    days: int = Query(3650, ge=1, le=3650),
    limit: int = Query(500, ge=1, le=5000),
):
    symbol = (ticker or "").strip().upper()
    rows = recent_records(provider=provider, category=category, symbol=symbol, days=days, limit=limit)
    return {
        "status": "ok",
        "ticker": symbol,
        "category": category,
        "provider": provider,
        "days": days,
        "count": len(rows),
        "records": rows,
    }


@router.post("/tickers/validate")
def validate_custom_ticker(request: CustomTickerRequest):
    ticker = (request.ticker or "").strip().upper()
    if not ticker or len(ticker) > 12 or not ticker.replace(".", "").replace("-", "").isalnum():
        return {"status": "error", "valid": False, "ticker": ticker, "message": "Ticker must be 1-12 letters/numbers, with optional dot or dash."}

    before = build_dashboard(ticker, "daily")
    before_points = int(before.get("summary", {}).get("price_points") or 0)
    if before_points > 0:
        watchlist = add_watchlist_ticker(ticker, source="sqlite_cache_validation")
        return {"status": "ok", "valid": True, "ticker": ticker, "source": "sqlite_cache", "message": f"{ticker} already has stored local data.", "watchlist": watchlist, "dashboard": before}

    result = RefreshOrchestrator().refresh_ticker(ticker)
    after = build_dashboard(ticker, "daily")
    quality = after.get("quality", {})
    valid = bool(quality.get("valid_for_workspace"))
    return {
        "status": "ok" if valid else "error",
        "valid": valid,
        "ticker": ticker,
        "source": "provider_refresh_then_sqlite" if valid else "provider_refresh_failed",
        "message": f"{ticker} validated and stored locally with {quality.get('coverage_score', 0)}/100 coverage." if valid else f"No usable price/quote data was returned for {ticker}; workspace not added.",
        "readiness": quality,
        "refresh_result": result,
        "watchlist": add_watchlist_ticker(ticker, source="provider_refresh_validation") if valid else get_watchlist_tickers(),
        "dashboard": after,
    }
