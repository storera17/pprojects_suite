from __future__ import annotations

from fastapi import APIRouter

from app.repositories.agent_runs_repository import finish_refresh_run, start_refresh_run
from app.repositories.watchlist_repository import get_watchlist_tickers
from app.schemas.common import RefreshRequest
from app.services.refresh_service import RefreshOrchestrator

router = APIRouter(tags=["refresh"])


@router.post("/refresh/run")
def refresh_run(request: RefreshRequest | None = None):
    tickers = [ticker.upper() for ticker in (request.tickers if request and request.tickers else get_watchlist_tickers())]
    run_id = start_refresh_run(tickers)
    try:
        result = RefreshOrchestrator().refresh_all(tickers)
        finish_refresh_run(run_id, "ok", "manual refresh completed", result)
        return result
    except Exception as exc:
        finish_refresh_run(run_id, "error", str(exc))
        return {"status": "error", "error": str(exc)}


@router.post("/refresh/ticker/{ticker}")
def refresh_ticker(ticker: str):
    try:
        result = RefreshOrchestrator().refresh_ticker(ticker.upper())
        return {"status": "ok", "ticker": ticker.upper(), "result": result}
    except Exception as exc:
        return {"status": "error", "ticker": ticker.upper(), "error": str(exc)}
