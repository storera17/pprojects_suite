from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import MarketPulseModel, StatusResponse


class CustomTickerRequest(MarketPulseModel):
    ticker: str = Field(min_length=1, max_length=12)


class TickerAvailabilityResponse(StatusResponse):
    ticker: str
    has_data: bool = False
    record_count: int = 0
    categories: dict[str, int] = Field(default_factory=dict)
    providers: dict[str, int] = Field(default_factory=dict)


class TickerRecordsResponse(StatusResponse):
    ticker: str
    count: int = 0
    records: list[dict[str, Any]] = Field(default_factory=list)
