from __future__ import annotations

from typing import Any

from app.schemas.common import MarketPulseModel, StatusResponse


class DashboardSummary(MarketPulseModel):
    latest_price: float | None = None
    latest_price_provider: str | None = None
    latest_quote: float | None = None
    latest_quote_provider: str | None = None
    executive_takeaway: str | None = None


class DashboardResponse(StatusResponse):
    ticker: str
    period: str
    summary: DashboardSummary | dict[str, Any]
