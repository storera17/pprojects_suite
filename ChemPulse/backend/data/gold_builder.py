from __future__ import annotations

from pathlib import Path

from backend.data.schemas import GOLD_SCHEMA_SQL
from backend.config import get_config
from backend.data.db import get_connection
from backend.data.scaffold_registry import ScaffoldRegistry