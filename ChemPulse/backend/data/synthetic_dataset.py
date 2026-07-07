from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import json

import duckdb

from backend.core.paths import storage_dir
from backend.data.schemas import CORE_INGESTION_SCHEMA_SQL, GOLD_SCHEMA_SQL
