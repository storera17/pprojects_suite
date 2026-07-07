from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any

import duckdb

from backend.chemistry.rdkit_engine import ChemistryEngine
from backend.data.db import get_connection, get_db_path
from backend.data.schemas import GOLD_SCHEMA_SQL