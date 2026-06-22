from __future__ import annotations

from typing import Any


class MarketPulseError(RuntimeError):
    """Base domain error for service and repository code."""


class AutoAgentRunBusyError(MarketPulseError):
    def __init__(self, active_run: dict[str, Any], message: str):
        super().__init__(message)
        self.active_run = active_run
