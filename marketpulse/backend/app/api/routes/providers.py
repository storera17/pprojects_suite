from __future__ import annotations

from fastapi import APIRouter

from app.repositories.provider_status_repository import get_provider_statuses
from app.repositories.records_repository import recent_records
from app.services.refresh_service import configured_provider_keys

router = APIRouter(tags=["providers"])


@router.get("/providers/status")
def providers_status():
    providers = get_provider_statuses()
    configured_keys = configured_provider_keys()
    seen = set()
    for provider in providers:
        name = provider.get("provider")
        seen.add(name)
        configured = configured_keys.get(name)
        provider["api_key_configured"] = configured
        if provider.get("status") == "not_configured" and configured:
            provider["status"] = "needs_refresh"
            provider["message"] = (
                f"{name} API key is configured now, but provider health reflects an older cached status. "
                "Run the Auto Cached Agent or refresh this provider to update ingestion health."
            )
    for name, configured in configured_keys.items():
        if name not in seen:
            providers.append(
                {
                    "provider": name,
                    "status": "not_run" if configured else "not_configured",
                    "message": "Configured but no ingestion run has been recorded yet." if configured else "API key is not configured.",
                    "api_key_configured": configured,
                    "cache_source": "none",
                    "cache_fresh": False,
                    "cache_record_count": 0,
                    "fallback_active": False,
                    "rate_limit_fallback": False,
                }
            )
    return {"status": "ok", "providers": sorted(providers, key=lambda row: row.get("provider") or "")}


@router.get("/monitoring/api-usage")
def api_usage(limit: int = 100):
    return {"status": "ok", "providers": get_provider_statuses(), "recent_records": recent_records(limit=limit)}


@router.get("/source-reliability")
def source_reliability():
    return {
        "polygon": {"type": "market_data", "reliability": "high when key/plan available"},
        "finnhub": {"type": "quote", "reliability": "high when key/plan available"},
        "alpha_vantage": {"type": "market_data", "reliability": "good but rate-limited on free plans"},
        "fred": {"type": "macro", "reliability": "official macroeconomic source"},
        "marketaux": {"type": "news", "reliability": "provider-dependent"},
        "nytimes": {"type": "news", "reliability": "publisher search API"},
        "serpstack": {"type": "search", "reliability": "search-result dependent"},
        "stockdata": {"type": "quote_news", "reliability": "provider-dependent"},
    }
