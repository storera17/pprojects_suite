from __future__ import annotations

from fastapi import APIRouter, Query

from app.repositories.records_repository import recent_records
from app.services.census_service import search_census_metadata
from app.services.refresh_service import RefreshOrchestrator

router = APIRouter(tags=["macro"])


@router.get("/macro/census/discovery")
def census_macro_discovery(
    q: str | None = Query(default=None, description="Free-text search for datasets or indicator metadata."),
    kind: str = Query(default="all", pattern="^(all|datasets|indicators)$"),
    dataset_limit: int = Query(default=8, ge=1, le=20),
    indicator_limit: int = Query(default=14, ge=1, le=40),
):
    try:
        return search_census_metadata(query=q, kind=kind, dataset_limit=dataset_limit, indicator_limit=indicator_limit)
    except Exception as exc:
        return {
            "status": "error",
            "source": "census_public_metadata",
            "query": str(q or "").strip(),
            "kind": kind,
            "error": str(exc),
            "dataset_matches": [],
            "indicator_matches": [],
            "featured_queries": [],
        }


@router.get("/crypto/tokens")
def crypto_token_prices():
    refresh = RefreshOrchestrator()
    alchemy = refresh.crypto_fx.alchemy()
    coinlayer = refresh.crypto_fx.coinlayer()
    return {"status": "ok", "alchemy": alchemy, "coinlayer": coinlayer, "cached_records": recent_records(category="crypto", days=30, limit=100)}


@router.get("/forex/rates")
def forex_rates():
    refresh = RefreshOrchestrator()
    currencylayer = refresh.crypto_fx.currencylayer()
    fixer = refresh.crypto_fx.fixer()
    return {"status": "ok", "currencylayer": currencylayer, "fixer": fixer, "cached_records": recent_records(category="fx", days=30, limit=100)}
