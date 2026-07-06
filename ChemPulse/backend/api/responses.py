from __future__ import annotations

from typing import Any, Callable
import json

from starlette.requests import Request
from starlette.responses import Response

def json_response(content: Any, status_code: int = 200) -> Response:
    return Response(
        json.dumps(content, allow_nan=False),
        status_code=status_code,
        media_type="application/json",
        headers=_cors_headers(),
    )
    
def javascript_response(source: str) -> Response:
    return Response(
        source,
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Private-Network": "true",
            "Cache-Control": "no-store",
            "Cross-Origin-Resource-Policy": "cross-origin",
        },
    )
    
def static_response(content: str, media_type: str) -> Response:
    return Response(content, media_type=media_type, headers=_cors_headers())

def static_headers() -> dict[str, str]:
    return _cors_headers()

def safe_json_or_error(loader: Callable[[], Any]) -> Response:
    try:
        return json_response(safe_dashboard_payload(loader()))
    except Exception as exc:  # noqa: BLE001
        return json_response(
            {
                "items": [],
                "metadata": {
                    "record_count": 0,
                    "source": "error",
                    "last_updated": "",
                    "empty_state_reason": f"ChemPulse data unavailable: {safe_error(exc)}",
                    "last_error": safe_error(exc),
                },
            },
            status_code=500,
        )