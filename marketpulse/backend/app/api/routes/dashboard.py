from __future__ import annotations
from ast import pattern
from fastapi import APIRouter, Query
from app.repositories.records_repository import db_summary
from app.services.dashboard_service import build_dashboard

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard/{ticker}")
def get_dashboard(ticker: str = "SPY",
                  period: str = Query("daily",
                                      pattern="^(daily|weekly|monthly)$")):
    return build_dashboard(ticker, 
                           period)

@router.get("/dashboard/bootstrap/{ticker}")
def dashboard_bootstrap(ticker: str = "SPY",
                        period: str = Query("daily",
                                            pattern="^(daily|weekly|monthly)$")):
    return build_dashboard(ticker, 
                           period)

@router.get("/dashboard/summary")
def dashboard_summary(ticker: str = "SPY",
                          period: str = "daily"):
    dashboard_payload = build_dashboard(ticker=ticker, 
                                        period=period)
    return {"status": "ok",
            "summary": dashboard_payload.get("summary",
                                             {}),
            "db_summary": db_summary()}