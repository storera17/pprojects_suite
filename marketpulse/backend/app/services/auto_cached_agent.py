from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.repositories.agent_runs_repository import (
    finish_auto_agent_run,
    get_auto_agent_latest,
    get_auto_agent_runs,
    reconcile_stale_auto_agent_runs,
    start_auto_agent_run,
)
from app.repositories.provider_status_repository import get_provider_statuses
from app.repositories.records_repository import cache_snapshot
from app.repositories.watchlist_repository import get_watchlist_tickers
from app.services.dashboard_service import build_dashboard
from app.services.refresh_service import RefreshOrchestrator
from app.services.report_service import build_watchlist_brief, persist_daily_brief

TICKER_CACHE_PLAN = [
    {"provider": "polygon", "category": "price", "label": "Polygon daily prices", "critical": True, "limit": 365},
    {"provider": "alpha_vantage", "category": "price", "label": "Alpha Vantage daily prices", "critical": True, "limit": 100},
    {"provider": "finnhub", "category": "quote", "label": "Finnhub quote", "critical": True, "limit": 5},
    {"provider": "stockdata", "category": "quote", "label": "StockData quote", "critical": False, "limit": 10},
    {"provider": "stockdata", "category": "news", "label": "StockData news", "critical": False, "limit": 10},
    {"provider": "marketaux", "category": "news", "label": "Marketaux news", "critical": False, "limit": 20},
    {"provider": "nytimes", "category": "news", "label": "NYTimes news", "critical": False, "limit": 20},
    {"provider": "serpstack", "category": "search", "label": "Serpstack search", "critical": False, "limit": 20},
]

GLOBAL_CACHE_PLAN = [
    {"provider": "fred", "category": "macro", "symbol": None, "label": "FRED macro", "critical": False, "limit": 100},
    {"provider": "coinlayer", "category": "crypto", "symbol": None, "label": "Coinlayer crypto", "critical": False, "limit": 50},
    {"provider": "alchemy", "category": "crypto", "symbol": None, "label": "Alchemy crypto", "critical": False, "limit": 50},
    {"provider": "currencylayer", "category": "fx", "symbol": None, "label": "Currencylayer FX", "critical": False, "limit": 50},
    {"provider": "fixer", "category": "fx", "symbol": None, "label": "Fixer FX", "critical": False, "limit": 50},
]


def _ttl_seconds() -> int:
    try:
        return int(settings.provider_cache_ttl_seconds)
    except Exception:
        return 86400


class AutoCachedAgent:
    def __init__(self):
        self.ttl_seconds = _ttl_seconds()
        self.refresh = RefreshOrchestrator()

    def inspect_ticker(self, ticker: str) -> dict[str, Any]:
        symbol = ticker.upper().strip()
        categories = []
        stale_count = 0
        missing_count = 0
        fresh_count = 0
        critical_ready = False
        for item in TICKER_CACHE_PLAN:
            snapshot = cache_snapshot(item["provider"], item["category"], symbol, ttl_seconds=self.ttl_seconds, limit=item.get("limit", 100))
            row = {
                "ticker": symbol,
                "provider": item["provider"],
                "category": item["category"],
                "label": item["label"],
                "critical": bool(item.get("critical")),
                "count": snapshot.get("count", 0),
                "fresh": bool(snapshot.get("fresh")),
                "cache_age_minutes": snapshot.get("cache_age_minutes"),
                "cache_collected_at": snapshot.get("cache_collected_at"),
                "state": "fresh" if snapshot.get("fresh") else ("stale" if snapshot.get("count") else "missing"),
            }
            categories.append(row)
            if row["state"] == "fresh":
                fresh_count += 1
            elif row["state"] == "missing":
                missing_count += 1
            else:
                stale_count += 1
            if row["critical"] and row["count"] > 0:
                critical_ready = True
        stale_or_missing = [row for row in categories if row["state"] != "fresh"]
        return {
            "ticker": symbol,
            "ttl_seconds": self.ttl_seconds,
            "state": "fresh" if not stale_or_missing else ("partial" if critical_ready else "needs_refresh"),
            "critical_ready": critical_ready,
            "fresh_categories": fresh_count,
            "stale_categories": stale_count,
            "missing_categories": missing_count,
            "refresh_needed": bool(stale_or_missing),
            "categories": categories,
        }

    def inspect_global(self) -> dict[str, Any]:
        categories = []
        for item in GLOBAL_CACHE_PLAN:
            snapshot = cache_snapshot(item["provider"], item["category"], item.get("symbol"), ttl_seconds=self.ttl_seconds, limit=item.get("limit", 100))
            categories.append(
                {
                    "provider": item["provider"],
                    "category": item["category"],
                    "label": item["label"],
                    "count": snapshot.get("count", 0),
                    "fresh": bool(snapshot.get("fresh")),
                    "cache_age_minutes": snapshot.get("cache_age_minutes"),
                    "cache_collected_at": snapshot.get("cache_collected_at"),
                    "state": "fresh" if snapshot.get("fresh") else ("stale" if snapshot.get("count") else "missing"),
                }
            )
        return {"categories": categories, "refresh_needed": any(category["state"] != "fresh" for category in categories)}

    def status(self, tickers: list[str] | None = None) -> dict[str, Any]:
        symbols = [ticker.upper() for ticker in (tickers or get_watchlist_tickers())]
        inspected = [self.inspect_ticker(symbol) for symbol in symbols]
        global_state = self.inspect_global()
        latest = get_auto_agent_latest()
        provider_statuses = get_provider_statuses()
        fallback_count = sum(1 for provider in provider_statuses if provider.get("fallback_active") or provider.get("rate_limit_fallback"))
        stale_categories = sum(item["stale_categories"] + item["missing_categories"] for item in inspected)
        stale_categories += sum(1 for category in global_state["categories"] if category["state"] != "fresh")
        return {
            "status": "ok",
            "enabled": bool(settings.auto_refresh_enabled),
            "mode": "auto_cached_agent",
            "ttl_seconds": self.ttl_seconds,
            "interval_minutes": int(settings.auto_refresh_interval_minutes),
            "tickers": symbols,
            "last_run": latest,
            "fallback_count": fallback_count,
            "stale_categories": stale_categories,
            "refresh_needed": bool(stale_categories),
            "ticker_states": inspected,
            "global_state": global_state,
            "message": "Auto Cached Agent is monitoring SQLite freshness and will refresh stale/missing categories only.",
        }

    def run(self, tickers: list[str] | None = None, force: bool = False, mode: str = "manual") -> dict[str, Any]:
        symbols = [ticker.upper() for ticker in (tickers or get_watchlist_tickers())]
        try:
            run_id = start_auto_agent_run(mode=mode, tickers=symbols, message=f"{mode} auto cached agent run started")
        except Exception as exc:
            active_run = getattr(exc, "active_run", None)
            if active_run is not None:
                return {"status": "busy", "mode": mode, "tickers": symbols, "message": str(exc), "active_run": active_run}
            raise

        started = datetime.now(timezone.utc)
        result: dict[str, Any] = {
            "status": "running",
            "mode": mode,
            "run_id": run_id,
            "tickers": symbols,
            "ticker_results": {},
            "global_result": None,
            "provider_calls_skipped": 0,
            "stale_categories": 0,
            "refreshed_tickers": 0,
            "fallbacks_used": 0,
        }
        try:
            for ticker in symbols:
                inspection = self.inspect_ticker(ticker)
                result["stale_categories"] += inspection["stale_categories"] + inspection["missing_categories"]
                result["provider_calls_skipped"] += inspection["fresh_categories"]
                if force or inspection["refresh_needed"]:
                    refresh_result = self.refresh.refresh_ticker(ticker, force=force)
                    refreshed_dashboard = build_dashboard(ticker, "daily", ttl_seconds=self.ttl_seconds)
                    result["ticker_results"][ticker] = {
                        "action": "refreshed" if inspection["refresh_needed"] or force else "checked",
                        "before": inspection,
                        "refresh_result": refresh_result,
                        "quality": refreshed_dashboard.get("quality", {}),
                    }
                    result["refreshed_tickers"] += 1
                else:
                    result["ticker_results"][ticker] = {"action": "skipped_fresh_cache", "before": inspection}
            global_inspection = self.inspect_global()
            result["stale_categories"] += sum(1 for category in global_inspection["categories"] if category["state"] != "fresh")
            result["global_result"] = self.refresh.refresh_macro_context(force=force) if force or global_inspection["refresh_needed"] else {"action": "skipped_fresh_cache", "before": global_inspection}

            statuses = get_provider_statuses()
            result["fallbacks_used"] = sum(1 for provider in statuses if provider.get("fallback_active") or provider.get("rate_limit_fallback"))

            try:
                brief = build_watchlist_brief(symbols, "daily")
                saved = persist_daily_brief(brief, run_id=run_id)
                result["daily_brief"] = {
                    "saved": True,
                    "brief_id": saved["brief_id"],
                    "ticker_reports_saved": len(saved["ticker_report_ids"]),
                    "report_date": saved["report_date"],
                }
            except Exception as exc:
                result["daily_brief"] = {"saved": False, "error": str(exc)}

            result["status"] = "ok"
            result["finished_at"] = datetime.now(timezone.utc).isoformat()
            result["duration_seconds"] = round((datetime.now(timezone.utc) - started).total_seconds(), 2)
            result["message"] = f"Checked {len(symbols)} tickers; refreshed {result['refreshed_tickers']} ticker workspaces; skipped {result['provider_calls_skipped']} fresh categories."
            finish_auto_agent_run(run_id, "ok", result, result["message"])
            return result
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            finish_auto_agent_run(run_id, "error", result, str(exc))
            return result

    def runs(self, limit: int = 25) -> dict[str, Any]:
        return {"status": "ok", "runs": get_auto_agent_runs(limit)}
