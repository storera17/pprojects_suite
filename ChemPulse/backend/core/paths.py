from __future__ import annotations

import os
import sys
from pathlib import Path

def project_root() -> Path:
    return Path(__file__).resolve().parents[2]
