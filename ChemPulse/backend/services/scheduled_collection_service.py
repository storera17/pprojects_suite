from __future__ import annotations

import threading
import uuid
import re
import os
import subprocess
import sys
import json
import time
from datetime import datetime, time as day_time, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.agents.core_publication_agent import DEFAULT_QUERY, CorePublicationAgent, settings_from_env
from backend.config import get_secret_env, is_api_key_configured
from backend.data.core_publication_repository import CorePublicationRepository
from backend.integrations.core_api import CoreApiClient

_scheduler_lock = threading.Lock()
_scheduler_registered = False
_scheduler_timer: threading.Timer | None = None
_running = False
_next_run_at: datetime | None = None


class ScheduledCollectionService:
    @staticmethod
    def register_once() -> dict[str, Any]:
        global _scheduler_registered, _scheduler_timer, _next_run_at
        with _scheduler_lock:
            if not _scheduler_registered:
                _scheduler_registered = True
                if ScheduledCollectionService.enabled():
                    _next_run_at = _next_daily_run_at()
                    delay = max(1.0, (_next_run_at - datetime.now()).total_seconds())
                    _scheduler_timer = threading.Timer(delay, _scheduled_run)
                    _scheduler_timer.daemon = True
                    _scheduler_timer.start()
        return ScheduledCollectionService.status()

    @staticmethod
    def enabled() -> bool:
        return get_secret_env("CHEMPULSE_COLLECTION_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}

    @staticmethod
    def is_running() -> bool:
        return _running or _collection_marker_active()

    @staticmethod
    def cached_status() -> dict[str, Any]:
        return _read_status_cache() or _status_cache_default()

    @staticmethod
    def status(force_refresh: bool = False) -> dict[str, Any]:
        if ScheduledCollectionService.enabled() and not _scheduler_registered:
            ScheduledCollectionService.register_once()

        if not force_refresh and ScheduledCollectionService.is_running():
            return _running_status_from_cache(_read_status_cache())

        try:
            CorePublicationRepository.reconcile_orphaned_runs(max_age_hours=_stale_running_hours())
            run_status = CorePublicationRepository.agent_run_status()
            latest_run = run_status.get("latest_run") or {}
            if latest_run.get("status") == "running" and not _running and _is_stale_running(latest_run):
                CorePublicationRepository.reconcile_orphaned_runs(max_age_hours=_stale_running_hours())
                run_status = CorePublicationRepository.agent_run_status()
                latest_run = run_status.get("latest_run") or {}
            last_success = run_status.get("last_success") or {}
            last_insufficient = run_status.get("last_insufficient") or {}
            last_failure = run_status.get("last_failure") or {}
            records_processed = int(latest_run.get("records_processed") or 0)
            latest_error = str(latest_run.get("error_summary") or "")
            status = {
                "configured": is_api_key_configured(),
                "enabled": ScheduledCollectionService.enabled(),
                "running": _running or latest_run.get("status") == "running",
                "last_success_at": _format_dt(last_success.get("finished_at")),
                "last_insufficient_at": _format_dt(last_insufficient.get("finished_at")),
                "last_failure_at": _format_dt(last_failure.get("finished_at")),
                "last_run_started_at": _format_dt(latest_run.get("started_at")),
                "last_run_finished_at": _format_dt(latest_run.get("finished_at")),
                "last_run_status": str(latest_run.get("status") or "never run"),
                "last_run_query": str(latest_run.get("query") or ""),
                "last_run_downloaded_count": int(latest_run.get("downloaded_count") or 0),
                "last_run_inserted_count": int(latest_run.get("inserted_count") or 0),
                "last_run_updated_count": int(latest_run.get("updated_count") or 0),
                "last_run_diagnosis_path": str(latest_run.get("diagnosis_path") or ""),
                "records_processed": records_processed,
                "last_error": latest_error,
                "next_run_at": _format_dt(_next_run_at),
            }
            _write_status_cache(status)
            return status
        except Exception as exc:
            cached = _read_status_cache()
            if not cached:
                raise
            fallback = {
                **cached,
                "configured": is_api_key_configured(),
                "enabled": ScheduledCollectionService.enabled(),
                "running": ScheduledCollectionService.is_running(),
                "next_run_at": _format_dt(_next_run_at),
            }
            if not fallback.get("last_error"):
                fallback["last_error"] = _safe_error(exc)
            return _running_status_from_cache(fallback) if ScheduledCollectionService.is_running() else fallback

    @staticmethod
    def run_now(client: Any | None = None) -> dict[str, Any]:
        global _running
        with _scheduler_lock:
            if _running:
                return {"status": "already_running", "message": "ChemPulse collection is already running."}
            _running = True
            _write_status_cache(_running_status_from_cache(_read_status_cache()))
        try:
            return _run_collection(client)
        finally:
            _running = False

    @staticmethod
    def trigger_now() -> dict[str, Any]:
        global _running
        with _scheduler_lock:
            if _running:
                return {"status": "already_running", "message": "ChemPulse collection is already running."}
            _running = True
            _write_collection_marker("running")
            _write_status_cache(_running_status_from_cache(_read_status_cache()))

        def launch_and_watch() -> None:
            global _running
            latest_run_id = _latest_run_id()
            try:
                process = _start_external_collection()
                exit_code = _wait_for_external_collection(process)
                if exit_code != 0 and _latest_run_id() == latest_run_id:
                    _record_launcher_failure(f"External ChemPulse collection exited with code {exit_code}.")
            except Exception as exc:
                if _latest_run_id() == latest_run_id:
                    _record_launcher_failure(_safe_error(exc))
            finally:
                _write_collection_marker("finished")
                _running = False

        launcher = threading.Thread(target=launch_and_watch, name="chempulse-manual-collection-launch", daemon=True)
        launcher.start()
        return {
            "status": "started",
            "message": "ChemPulse collection started.",
        }


def _scheduled_run() -> None:
    global _scheduler_timer, _next_run_at
    try:
        ScheduledCollectionService.run_now()
    finally:
        with _scheduler_lock:
            if ScheduledCollectionService.enabled():
                _next_run_at = _next_daily_run_at()
                delay = max(1.0, (_next_run_at - datetime.now()).total_seconds())
                _scheduler_timer = threading.Timer(delay, _scheduled_run)
                _scheduler_timer.daemon = True
                _scheduler_timer.start()


def _run_collection(client: Any | None = None) -> dict[str, Any]:
    try:
        # Meta-OS M7: route the scheduled/manual run through the ChemPulse adapter, which
        # delegates dedup/backward-search/cursor/reports to CorePublicationAgent and adds
        # the 25-unique target, topic compilation, dated folders, and visible DB fields.
        # Settings are resolved here (preserving this module's settings_from_env seam) and
        # passed in, so missing-key handling stays in this try/except.
        from backend.services.chempulse_publication_job import ChemPulsePublicationJob

        api_settings, agent_settings = settings_from_env()
        result = ChemPulsePublicationJob(
            client=client, api_settings=api_settings, agent_settings=agent_settings
        ).run()
        final_status = ScheduledCollectionService.status(force_refresh=True)
        return {**result, "agent_status": final_status}
    except Exception as exc:
        if not is_api_key_configured():
            _record_configuration_failure(_safe_error(exc))
        final_status = ScheduledCollectionService.status(force_refresh=True)
        return {"status": "failed", "error": _safe_error(exc), "agent_status": final_status}


def _next_daily_run_at() -> datetime:
    configured = get_secret_env("CHEMPULSE_COLLECTION_TIME", "03:15").strip() or "03:15"
    try:
        hour_text, minute_text = (configured.split(":", 1) + ["00"])[:2]
        hour = int(hour_text)
        minute = int(minute_text)
        if hour not in range(24) or minute not in range(60):
            raise ValueError(configured)
    except ValueError:
        hour = 3
        minute = 15
    target = day_time(hour=hour, minute=minute)
    now = datetime.now()
    candidate = datetime.combine(now.date(), target)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def _stale_running_hours() -> float:
    value = get_secret_env("CHEMPULSE_COLLECTION_STALE_MINUTES", "30").strip()
    try:
        return max(float(value), 1.0) / 60.0
    except ValueError:
        return 0.5


def _is_stale_running(latest_run: dict[str, Any]) -> bool:
    started_at = latest_run.get("started_at")
    if not isinstance(started_at, datetime):
        return False
    return datetime.now() - started_at > timedelta(hours=_stale_running_hours())


def _format_dt(value: Any) -> str:
    if not value:
        return "Never"
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _safe_error(exc: Exception) -> str:
    text = re.sub(r"CORE_API_KEY\s*=\s*[^,\s;]+", "literature API key [redacted]", str(exc))
    text = text.replace("CORE_API_KEY", "literature API key")
    text = re.sub(r"sk-[A-Za-z0-9_\-]+", "[redacted]", text)
    text = re.sub(r"LSl[A-Za-z0-9_\-]+", "[redacted]", text)
    return text


def _record_configuration_failure(error: str) -> None:
    run_id = str(uuid.uuid4())
    query = DEFAULT_QUERY.format(since=datetime.now(timezone.utc).date().isoformat(), year=datetime.now(timezone.utc).year)
    CorePublicationRepository.start_run(run_id=run_id, query=query, requested_limit=0, page_size=0)
    CorePublicationRepository.finish_run(run_id, "failed", 0, 0, error)


def _record_launcher_failure(error: str) -> None:
    _write_collection_log(f"Recording collection launcher failure: {error}")
    _record_configuration_failure(error)


def _latest_run_id() -> str:
    try:
        latest_run = (CorePublicationRepository.agent_run_status().get("latest_run") or {})
        return str(latest_run.get("run_id") or "")
    except Exception:
        return ""


def _collection_marker_path() -> Path:
    root = _project_root()
    storage_dir = Path(get_secret_env("CHEMPULSE_STORAGE_DIR", str(root / "storage")))
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / ".collection-running.json"


def _status_cache_path() -> Path:
    return _collection_marker_path().with_name(".collection-status.json")


def _write_collection_marker(status: str) -> None:
    payload = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    _collection_marker_path().write_text(json.dumps(payload), encoding="utf-8")


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
        path.write_text(json.dumps(status, ensure_ascii=True), encoding="utf-8")
    except OSError:
        pass


def _status_cache_default() -> dict[str, Any]:
    return {
        "configured": is_api_key_configured(),
        "enabled": ScheduledCollectionService.enabled(),
        "running": False,
        "last_success_at": "Never",
        "last_insufficient_at": "Never",
        "last_failure_at": "Never",
        "last_run_started_at": "Never",
        "last_run_finished_at": "Never",
        "last_run_status": "never run",
        "last_run_query": "",
        "last_run_downloaded_count": 0,
        "last_run_inserted_count": 0,
        "last_run_updated_count": 0,
        "last_run_diagnosis_path": "",
        "records_processed": 0,
        "last_error": "",
        "next_run_at": _format_dt(_next_run_at),
    }


def _running_status_from_cache(cached: dict[str, Any] | None) -> dict[str, Any]:
    base = {**_status_cache_default(), **(cached or {})}
    base["configured"] = is_api_key_configured()
    base["enabled"] = ScheduledCollectionService.enabled()
    base["running"] = True
    base["last_run_status"] = "running"
    base["last_run_finished_at"] = "Refresh pending"
    base["next_run_at"] = _format_dt(_next_run_at) if _next_run_at else "Refresh pending"
    return base


def _collection_marker_active(max_age_seconds: int | None = None) -> bool:
    marker = _collection_marker_path()
    if not marker.exists():
        return False
    try:
        payload = json.loads(marker.read_text(encoding="utf-8") or "{}")
        if payload.get("status") != "running":
            marker.unlink(missing_ok=True)
            return False
        age = datetime.now(timezone.utc).timestamp() - marker.stat().st_mtime
        max_age_seconds = max_age_seconds or _collection_marker_max_age_seconds()
        if age <= max_age_seconds:
            return True
        marker.unlink(missing_ok=True)
    except (OSError, json.JSONDecodeError):
        return False
    return False


def _start_external_collection() -> subprocess.Popen:
    root = _project_root()
    storage_dir = Path(get_secret_env("CHEMPULSE_STORAGE_DIR", str(root / "storage")))
    log_dir = storage_dir / "manual-runs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stdout_path = log_dir / f"manual-core-collection-{timestamp}.log"
    stderr_path = log_dir / f"manual-core-collection-{timestamp}.err.log"
    env = os.environ.copy()
    env.setdefault("CHEMPULSE_STORAGE_DIR", str(storage_dir))
    env.setdefault("CHEMPULSE_REPORT_DIR", str(storage_dir / "reports"))
    env["PYTHONPATH"] = _prepend_pythonpath(root, env.get("PYTHONPATH", ""))

    script = root / "scripts" / "run_core_publication_agent.ps1"
    if os.name == "nt" and script.exists():
        command = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-NoProfile",
            "-File",
            str(script),
            "-ProjectRoot",
            str(root),
            "-Python",
            _agent_python_executable(root),
            "-StorageDir",
            str(storage_dir),
        ]
    else:
        command = [_agent_python_executable(root), "-m", "backend.agents.core_publication_agent"]

    _write_collection_log(f"Starting collection command: {_safe_command(command)}")

    stdout = stdout_path.open("ab")
    stderr = stderr_path.open("ab")
    try:
        return subprocess.Popen(
            command,
            cwd=root,
            env=env,
            stdout=stdout,
            stderr=stderr,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
    finally:
        stdout.close()
        stderr.close()


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_parent = Path(sys.executable).resolve().parent
        if (exe_parent / "runtime" / "python.exe").exists() or (exe_parent / "rxconfig.py").exists():
            return exe_parent
    return Path(__file__).resolve().parents[2]


def _agent_python_executable(root: Path) -> str:
    configured = get_secret_env("CHEMPULSE_COLLECTION_PYTHON", "").strip()
    if configured and Path(configured).exists():
        return configured

    bundled_python = root / "runtime" / "python.exe"
    if bundled_python.exists():
        return str(bundled_python)

    venv_python = root / ".venv" / "Scripts" / "python.exe"
    if os.name == "nt" and venv_python.exists():
        return str(venv_python)

    return sys.executable


def _prepend_pythonpath(root: Path, existing: str) -> str:
    if not existing:
        return str(root)
    return f"{root}{os.pathsep}{existing}"


def _write_collection_log(message: str) -> None:
    try:
        storage_dir = _collection_marker_path().parent
        with (storage_dir / "collection-launcher.log").open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{datetime.now(timezone.utc).isoformat()}] {message}\n")
    except OSError:
        pass


def _safe_command(command: list[str]) -> str:
    return " ".join(str(part) if " " not in str(part) else f'"{part}"' for part in command)


def _wait_for_external_collection(process: subprocess.Popen) -> int:
    poll = getattr(process, "poll", None)
    if callable(poll):
        while True:
            exit_code = poll()
            if exit_code is not None:
                return int(exit_code)
            _write_collection_marker("running")
            time.sleep(_collection_marker_heartbeat_seconds())
    return int(process.wait())


def _collection_marker_heartbeat_seconds() -> float:
    value = get_secret_env("CHEMPULSE_COLLECTION_MARKER_HEARTBEAT_SECONDS", "10").strip()
    try:
        return max(float(value), 1.0)
    except ValueError:
        return 10.0


def _collection_marker_max_age_seconds() -> int:
    value = get_secret_env("CHEMPULSE_COLLECTION_MARKER_MAX_AGE_SECONDS", "45").strip()
    try:
        return max(int(float(value)), 5)
    except ValueError:
        return 45
