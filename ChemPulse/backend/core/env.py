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
