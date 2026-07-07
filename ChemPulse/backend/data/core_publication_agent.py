from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any

import duckdb

from backend.data.db import get_connection
from backend.data.db import is_transient_duckdb_error
from backend.data.publication_relevance import MEDIUM_RELEVANCE_THRESHOLD, publication_matches_focus, publication_relevance
from backend.data.schemas import CORE_INGESTION_SCHEMA_SQL