from __future__ import annotations

import json
from typing import Any

from backend.config import get_config, is_api_key_configured
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.db import ensure_database_exists, get_connection, table_exists
from backend.services.payload_service import PayloadService
from backend.services.scheduled_collection_service import ScheduledCollectionService

class DesktopStatusService:
    @staticmethod
    def cached_status() -> dict[str, Any]:
        return _read_status_cache()

    @staticmethod
    def get_status() -> dict[str, Any]:
        if ScheduledCollectionService.is_running():
            return _running_status()
        config = get_config()
        errors: list[str] = []

        database_reachable = _database_reachable(errors)
        scaffold_database_loaded = _scaffold_database_loaded(errors) if database_reachable else False
        chemistry_engine_available = _chemistry_engine_available(errors)
        ai_agent_configured = is_api_key_configured()
        run_status = _agent_run_status(errors) if database_reachable else {}
        previous_payload = PayloadService.latest_payload() if database_reachable else PayloadService.latest_payload()
        agent_status = ScheduledCollectionService.status() if database_reachable else {}
        literature_table_available = _table_available("bronze_core_publications", errors) if database_reachable else False
        scaffold_table_available = _table_available("scaffold_entries", errors) if database_reachable else False

        core_services_ready = database_reachable and scaffold_database_loaded and chemistry_engine_available
        if core_services_ready and ai_agent_configured:
            desktop_mode = "live"
        elif core_services_ready:
            desktop_mode = "fallback"
        else:
            desktop_mode = "offline"

        status = {
            "backend_reachable": core_services_ready,
            "database_reachable": database_reachable,
            "scaffold_database_loaded": scaffold_database_loaded,
            "scaffold_table_available": scaffold_table_available,
            "literature_table_available": literature_table_available,
            "chemistry_engine_available": chemistry_engine_available,
            "ai_literature_agent_configured": ai_agent_configured,
            "active_api_base_url": config.api_base_url,
            "last_database_update": _format_dt(run_status.get("last_database_update")),
            "last_successful_agent_run": _format_dt((run_status.get("last_success") or {}).get("finished_at")),
            "previous_payload_available": bool(previous_payload.get("available")),
            "previous_payload": previous_payload,
            "scheduled_collection_agent": agent_status,
            "last_connection_error": "; ".join(errors),
            "desktop_mode": desktop_mode,
        }
        _write_status_cache(status)
        return status


def _database_reachable(errors: list[str]) -> bool:
    try:
        ensure_database_exists()
        with get_connection(read_only=True) as con:
            con.execute("SELECT 1").fetchone()
        return True
    except Exception as exc:
        errors.append(f"ChemPulse database unavailable: {_safe_error(exc)}")
        return False


def _scaffold_database_loaded(errors: list[str]) -> bool:
    try:
        return table_exists("scaffold_entries")
    except Exception as exc:
        errors.append(f"ChemPulse scaffold database unavailable: {_safe_error(exc)}")
        return False


def _chemistry_engine_available(errors: list[str]) -> bool:
    try:
        from rdkit import Chem  # noqa: F401

        return True
    except Exception as exc:
        errors.append(f"ChemPulse chemistry engine unavailable: {_safe_error(exc)}")
        return False


def _agent_run_status(errors: list[str]) -> dict[str, Any]:
    try:
        return CorePublicationRepository.agent_run_status()
    except Exception as exc:
        errors.append(f"ChemPulse literature-agent status unavailable: {_safe_error(exc)}")
        return {}


def _table_available(table_name: str, errors: list[str]) -> bool:
    try:
        return table_exists(table_name)
    except Exception as exc:
        errors.append(f"ChemPulse table check failed for {table_name}: {_safe_error(exc)}")
        return False


def _format_dt(value: Any) -> str:
    if not value:
        return "Never"
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _safe_error(exc: Exception) -> str:
    return str(exc).replace("CORE_API_KEY", "literature API key")


def _status_cache_path():
    return get_config().storage_dir / ".desktop-status.json"


def _status_cache_default() -> dict[str, Any]:
    return {
        "backend_reachable": True,
        "database_reachable": True,
        "scaffold_database_loaded": True,
        "scaffold_table_available": True,
        "literature_table_available": True,
        "chemistry_engine_available": True,
        "ai_literature_agent_configured": is_api_key_configured(),
        "active_api_base_url": get_config().api_base_url,
        "last_database_update": "Never",
        "last_successful_agent_run": "Never",
        "previous_payload_available": False,
        "previous_payload": {},
        "scheduled_collection_agent": ScheduledCollectionService.cached_status(),
        "last_connection_error": "",
        "desktop_mode": "live" if is_api_key_configured() else "fallback",
    }


def _read_status_cache() -> dict[str, Any]:
    path = _status_cache_path()
    if not path.exists():
        return _status_cache_default()
    try:
        payload = json.loads(path.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError):
        return _status_cache_default()
    return {**_status_cache_default(), **payload}


def _write_status_cache(status: dict[str, Any]) -> None:
    path = _status_cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(status, ensure_ascii=True), encoding="utf-8")
    except OSError:
        pass


def _running_status() -> dict[str, Any]:
    cached = _read_status_cache()
    return {
        **cached,
        "ai_literature_agent_configured": is_api_key_configured(),
        "active_api_base_url": get_config().api_base_url,
        "scheduled_collection_agent": ScheduledCollectionService.status(),
        "last_connection_error": "Collection is running; database status refresh is paused to avoid DuckDB file contention.",
    }
