from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from app.core.config import settings
from app.repositories.watchlist_repository import get_watchlist_tickers
from app.services.auto_cached_agent import AutoCachedAgent

_task = None


def seconds_until_next_refresh() -> float:
    now = datetime.now()
    target = now.replace(hour=int(settings.refresh_hour), minute=int(settings.refresh_minute), second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return max(1.0, (target - now).total_seconds())


def seconds_until_next_scheduled_run() -> float:
    return seconds_until_next_refresh()


async def refresh_loop():
    while True:
        await asyncio.sleep(seconds_until_next_scheduled_run())
        try:
            if settings.auto_refresh_enabled:
                await asyncio.to_thread(AutoCachedAgent().run, get_watchlist_tickers(), True, "scheduled_daily_forced_agent")
        except Exception:
            pass


def start_scheduler():
    global _task
    if _task is None:
        _task = asyncio.create_task(refresh_loop())
    return _task
