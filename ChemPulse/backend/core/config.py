from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from backend.core.constants import LITERATURE_API_KEY_ENV
from backend.core.env import get_env_value
from backend.core.paths import project_root, storage_dir