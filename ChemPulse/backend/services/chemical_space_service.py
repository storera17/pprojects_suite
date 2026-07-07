from __future__ import annotations

import hashlib
import math
from typing import Any

import plotly.graph_objects as go

from backend.data.db import ensure_database_exists
from backend.data.repository import GoldRepository
from backend.data.scaffold_registry import ScaffoldRegistry