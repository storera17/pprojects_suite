from __future__ import annotations

from typing import Any

from backend.config import get_config, is_api_key_configured, masked_secret_status
from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.db import get_db_path
from backend.services.desktop_status_service import DesktopStatusService
from backend.services.scheduled_collection_service import ScheduledCollectionService
