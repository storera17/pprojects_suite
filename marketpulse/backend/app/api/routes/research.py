from __future__ import annotations

from fastapi import APIRouter, Query

from app.repositories.records_repository import latest_records
from app.services.refresh_service import RefreshOrchestrator

router = APIRouter(tags=["research"])


@router.get("/search/google")
def google_search(query: str = Query(default="stock market today"), ticker: str | None = None):
    return RefreshOrchestrator().serpstack.search(query=query, ticker=ticker)


@router.get("/market/stockdata/{ticker}")
def stockdata_market(ticker: str = "SPY"):
    return RefreshOrchestrator().stockdata.quote_and_news(ticker.upper())


@router.get("/records/latest/{provider}")
def latest_provider_records(provider: str, category: str | None = None, symbol: str | None = None, limit: int = 50):
    return {"status": "ok", "records": latest_records(provider, category, symbol, limit)}
