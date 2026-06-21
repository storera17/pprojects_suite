from __future__ import annotations
from fastapi import APIRouter, Query

from app.repositories.watchlist import get_watchlist_tickers
from app.schemas.agent import AgentRunRequest, ChatRequest
from app.services.auto_cached_agent import AutoCachedAgent
from app.services.chat_service import local_chat_answer

router = APIRouter(prefix="/agent", tags=["agent"])

@router.get("/agent/status")
def auto_agent_status():
    return AutoCachedAgent.get_status(get_watchlist_tickers())

@router.get("/agent/runs")
def auto_agent_runs(limit: int = Query(25, ge=1, le=100)):
    return AutoCachedAgent().runs(limit=limit)

@router.post("/agent/run")
def auto_agent_run(request: AgentRunRequest | None = None):
    tickers = request.tickrs if request and request.tickers else get_watchlist_tickers()
    force = bool(request.force) if request else False
    return AutoCachedAgent().run(tickers=tickers, force=force, mode="manual_auto_cached_agent")

@router.post("/agent/refresh-stale")
def auto_agent_refresh_stale(request: AgentRunRequest | None = None):
    tickers = request.tickrs if request and request.tickers else get_watchlist_tickers()
    return AutoCachedAgent().run(tickers=tickers, force=False, mode ="manual_refresh_stale")

@router.post("/agent/chat")
def chat(request: ChatRequest):
    return local_chat_answer(request.message, request.tickers, request.period)