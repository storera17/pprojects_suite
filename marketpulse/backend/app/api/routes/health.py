from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.repositories.provider_status_repository import get_provider_statuses
from app.repositories.records_repository import db_summary
from app.services.dashboard_service import build_dashboard
from app.services.refresh_service import configured_provider_keys

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "marketpulse-local-api",
        "mode": "local_sqlite_api_agents",
        "external_endpoint_required": False,
        "scheduled_refresh": f"{int(settings.refresh_hour):02d}:{int(settings.refresh_minute):02d}",
        "auto_cached_agent": {
            "enabled": bool(settings.auto_refresh_enabled),
            "schedule_mode": "daily_clock_time",
            "interval_minutes": int(settings.auto_refresh_interval_minutes),
            "minimum_interval_minutes": int(settings.auto_refresh_minimum_interval_minutes),
            "ttl_seconds": int(settings.provider_cache_ttl_seconds),
        },
    }


@router.get("/keys/status")
def keys_status():
    keys = {f"{name.upper()}_API_KEY": configured for name, configured in configured_provider_keys().items()}
    return {
        "status": "ok",
        "external_endpoint_required": False,
        "required_for_full_data": keys,
        "configured_count": sum(1 for value in keys.values() if value),
        "total_count": len(keys),
    }


@router.get("/cache/status/{ticker}")
def cache_status(ticker: str = "SPY"):
    dashboard = build_dashboard(ticker, "daily", ttl_seconds=int(settings.provider_cache_ttl_seconds))
    return {
        "status": "ok",
        "ticker": ticker.upper(),
        "external_calls_made": False,
        "cache_policy": {
            "dashboard_reads_sqlite_only": True,
            "refresh_cache_first": True,
            "rate_limit_uses_stale_sqlite": True,
            "ttl_seconds": settings.provider_cache_ttl_seconds,
        },
        "summary": dashboard.get("summary", {}),
        "providers": get_provider_statuses(),
        "db_summary": db_summary(),
    }


@router.get("/db/summary")
def database_summary():
    return {"status": "ok", "summary": db_summary()}
