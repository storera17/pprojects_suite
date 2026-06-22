from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import local_chat_answer
from app.services.dashboard_service import build_dashboard

router = APIRouter(tags=["users"])

_MEMORY: dict[str, dict] = {}
_ALERTS: dict[str, list[dict]] = {}


class PreferencesUpdate(BaseModel):
    updates: dict


class MemoryCreate(BaseModel):
    memory_type: str = "note"
    content: str


class AlertCreateRequest(BaseModel):
    type: str
    asset: str
    condition: str
    threshold: float
    message: str | None = None
    enabled: bool = True


class DashboardActionRequest(BaseModel):
    message: str
    ticker: str = "SPY"
    period: str = "daily"


@router.get("/users/{user_id}/dashboard")
def read_dashboard_preferences(user_id: str):
    return _MEMORY.setdefault(user_id, {"preferences": {}, "memory": []})["preferences"]


@router.patch("/users/{user_id}/dashboard")
def patch_dashboard_preferences(user_id: str, request: PreferencesUpdate):
    user = _MEMORY.setdefault(user_id, {"preferences": {}, "memory": []})
    user["preferences"].update(request.updates)
    return user["preferences"]


@router.get("/users/{user_id}/memory")
def read_memory(user_id: str):
    return {"memory": _MEMORY.setdefault(user_id, {"preferences": {}, "memory": []})["memory"]}


@router.post("/users/{user_id}/memory")
def create_memory(user_id: str, request: MemoryCreate):
    user = _MEMORY.setdefault(user_id, {"preferences": {}, "memory": []})
    record = request.model_dump()
    user["memory"].append(record)
    return record


@router.post("/users/{user_id}/dashboard/action")
def dashboard_action(user_id: str, request: DashboardActionRequest):
    return local_chat_answer(request.message, request.ticker, request.period)


@router.get("/users/{user_id}/alerts")
def read_alerts(user_id: str):
    return {"alerts": _ALERTS.get(user_id, [])}


@router.post("/users/{user_id}/alerts")
def add_alert(user_id: str, request: AlertCreateRequest):
    alert = request.model_dump()
    _ALERTS.setdefault(user_id, []).append(alert)
    return alert


@router.get("/users/{user_id}/daily-briefing")
def daily_briefing(user_id: str, ticker: str = "SPY", period: str = "daily"):
    dashboard = build_dashboard(ticker, period)
    return {"user_id": user_id, "ticker": ticker.upper(), "summary": dashboard.get("summary", {}), "topics": dashboard.get("topics", [])[:5]}
