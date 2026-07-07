from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from backend.config import get_config
from backend.data.core_publication_repository import ensure_core_ingestion_schema
from backend.data.db import get_connection, get_db_path
from backend.data.schemas import GOLD_SCHEMA_SQL

