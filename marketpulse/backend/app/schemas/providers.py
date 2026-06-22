from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import MarketPulseModel, StatusResponse


class ProviderStatusItem(MarketPulseModel):
    provider: str
    status: str
    message: str | None = None


class ProviderStatusResponse(StatusResponse):
    providers: list[ProviderStatusItem | dict[str, Any]] = Field(default_factory=list)


class KeyStatusResponse(StatusResponse):
    required_for_full_data: dict[str, bool] = Field(default_factory=dict)
    configured_count: int = 0
    total_count: int = 0
