from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.data.db import get_connection
from backend.data.schemas import CORE_INGESTION_SCHEMA_SQL
