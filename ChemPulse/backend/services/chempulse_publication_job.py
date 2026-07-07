from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.agents.core_publication_agent import CorePublicationAgent, settings_from_env
from backend.data import topics_repository
from backend.services import topics_service
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.db import query_records
from backend.integrations.core_api import CoreApiClient
from backend.core.paths import storage_dir

DEFAULT_TARGET_COUNT = 25

# Callable seam so tests inject a fake PDF fetcher (no network in tests).
PdfFetcher = Callable[[str, Path], Path | None]
AgentFactory = Callable[[Any, Any], CorePublicationAgent]
