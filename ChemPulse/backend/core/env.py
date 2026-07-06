from __future__ import annotations

import os
from pathlib import Path

from backend.core.paths import project_root

def project_env_path(root: Path | None = None) -> Path:
    return (root or project_root()) / ".env"

def read_project_env(root: Path | None = None) -> dict[str, str]:
    path = project_env_path(root)
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        key = name.strip()
        if not key:
            continue
        values[key] = _strip_wrapped_quotes(value.strip())
    return values

def get_env_value(name: str, default: str = "", *, root: Path | None = None) -> str:
    process_value = os.getenv(name)
    if process_value:
        return process_value

    user_value = _windows_user_env(name)
    if user_value:
        return user_value

    return read_project_env(root).get(name, default)

def _windows_user_env(name: str) -> str:
    if os.name != "nt":
        return ""

    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value).strip()
    except OSError:
        return ""
    
def _strip_wrapped_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
