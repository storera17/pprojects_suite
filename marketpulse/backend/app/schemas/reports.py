from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import MarketPulseModel, RefreshRequest, StatusResponse


class BriefGenerateRequest(RefreshRequest):
    pass


class StoredReport(MarketPulseModel):
    id: int | None = None
    report_text: str | None = None
    report_date: str | None = None
    scope: str | None = None
    ticker: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(StatusResponse):
    ticker: str
    period: str
    report: str
