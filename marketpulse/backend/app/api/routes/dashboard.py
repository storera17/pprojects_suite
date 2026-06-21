from __future__ import annotations

from fastapi import APIRouter, Query
from app.repositories.records_repository import db_summary
from app.services.dashboard_service import build_dashboard

router = APIRouter(tags=["dashboard"])

