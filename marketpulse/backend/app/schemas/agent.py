from __future__ import annotations

from app.schemas.common import MarketPulseModel, RefreshRequest


class ChatRequest(MarketPulseModel):
    message: str
    ticker: str = "SPY"
    period: str = "daily"
    user_id: str = "demo_user"


class AgentRunRequest(RefreshRequest):
    force: bool = False
