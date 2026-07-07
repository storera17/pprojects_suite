from __future__ import annotations

import json
from typing import Any

from backend.config import get_config, is_api_key_configured
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.db import ensure_database_exists, get_connection, table_exists
from backend.services.payload_service import PayloadService
from backend.services.scheduled_collection_service import ScheduledCollectionService
