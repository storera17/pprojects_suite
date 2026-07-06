from __future__ import annotations

import os
import sys
from pathlib import Path

def project_root() -> Path:
    return Path(__file__).resolve().parents[2]

def platform_app_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ChemPulse"
    if os.name == "nt":
        return Path(os.getenv("LOCALAPPDATA", str(project_root()))) / "ChemPulse"
    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home).expanduser() / "ChemPulse"
    return Path.home() / ".local" / "share" / "ChemPulse"

def storage_dir() -> Path:
    configured = os.getenv("CHEMPULSE_STORAGE_DIR")
    if configured:
        path = Path(configured).expanduser()
    elif getattr(sys, "frozen", False):
        path = platform_app_data_dir() / "storage"
    else:
        path = project_root() / "backend" / "storage"
    path.mkdir(parents=True, exist_ok=True)
    return path