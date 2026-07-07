from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from backend.data.core_publication_repository import CorePublicationRepository
from backend.data.repository import GoldRepository
from backend.services.manuscript_review_service import ManuscriptReviewService
from backend.services.publication_intelligence_service import PublicationIntelligenceService
from backend.services.research_pulse_service import ResearchPulseService