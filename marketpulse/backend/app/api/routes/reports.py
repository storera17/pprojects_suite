from __future__ import annotations

from fastapi import APIRouter, Query

from app.repositories.reports_repository import get_daily_reports, get_latest_daily_report
from app.repositories.watchlist_repository import get_watchlist_tickers
from app.schemas.common import RefreshRequest
from app.services.report_service import build_daily_report, build_watchlist_brief, persist_daily_brief

router = APIRouter(tags=["reports"])


@router.get("/reports/daily/{ticker}")
def daily_report(ticker: str = "SPY", period: str = "daily"):
    return build_daily_report(ticker, period)


@router.get("/reports/brief/latest")
def latest_daily_brief(scope: str = Query("watchlist", pattern="^(watchlist|ticker)$"), ticker: str | None = None):
    report = get_latest_daily_report(scope=scope, ticker=ticker)
    return {"status": "ok", "scope": scope, "ticker": (ticker or "").upper() or None, "report": report}


@router.get("/reports/brief/history")
def daily_brief_history(limit: int = Query(20, ge=1, le=200), scope: str | None = Query(None, pattern="^(watchlist|ticker)$"), ticker: str | None = None):
    return {"status": "ok", "reports": get_daily_reports(limit=limit, scope=scope, ticker=ticker)}


@router.post("/reports/brief/generate")
def generate_daily_brief(request: RefreshRequest | None = None):
    tickers = request.tickers if request and request.tickers else get_watchlist_tickers()
    brief = build_watchlist_brief([ticker.upper() for ticker in tickers], "daily")
    saved = persist_daily_brief(brief)
    return {"status": "ok", "saved": saved, "report": brief["report"], "tickers": brief["tickers"]}
