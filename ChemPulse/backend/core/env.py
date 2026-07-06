from __future__ import annotations

import os
from pathlib import Path

from backend.core.paths import project_root

def project_env_path(root: Path | None = None) -> Path:
    return (root or project_root()) / ".env"