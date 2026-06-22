from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MarketPulseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class StatusResponse(MarketPulseModel):
    status: str = "ok"


class MessageResponse(StatusResponse):
    message: str | None = None


class RefreshRequest(MarketPulseModel):
    tickers: list[str] | None = None


class GenericPayload(StatusResponse):
    data: dict[str, Any] = Field(default_factory=dict)
