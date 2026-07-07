from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import re
import uuid
from typing import Any

from backend.core.paths import storage_dir