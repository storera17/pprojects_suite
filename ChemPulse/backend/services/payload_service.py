from __future__ import annotations

from typing import Any

from backend.data.payload_repository import PayloadRepository, empty_payload


class PayloadService:
    @staticmethod
    def save_dashboard_payload(payload: dict[str, Any], source: str = "desktop-dashboard") -> dict[str, Any]:
        record_count = _record_count(payload)
        try:
            return PayloadRepository.save_payload(
                payload,
                source=source,
                status="valid",
                record_count=record_count,
            )
        except Exception as exc:
            return {
                **empty_payload(),
                "status": "failed",
                "last_error": str(exc).replace("CORE_API_KEY", "literature API key"),
                "message": "ChemPulse could not persist the latest dashboard payload.",
            }

    @staticmethod
    def latest_payload() -> dict[str, Any]:
        try:
            return PayloadRepository.latest_payload()
        except Exception as exc:
            return {
                **empty_payload(),
                "status": "failed",
                "last_error": str(exc).replace("CORE_API_KEY", "literature API key"),
                "message": "ChemPulse could not load the previous dashboard payload.",
            }


def _record_count(payload: dict[str, Any]) -> int:
    total = 0
    for key in ("top_scaffolds", "galaxy_points", "recent_publications", "research_pulse"):
        value = payload.get(key)
        if isinstance(value, list):
            total += len(value)
    return total