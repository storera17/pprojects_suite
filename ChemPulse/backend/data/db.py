from __future__ import annotations

from pathlib import Path
import os
import threading
import time
from typing import Any, Iterable

import duckdb

from backend.config import get_config
from backend.data.schemas import GOLD_SCHEMA_SQL, REQUIRED_GOLD_TABLES

_db_lock = threading.RLock()
