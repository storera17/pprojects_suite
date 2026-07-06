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

async def request_payload(request: Request) -> dict[str, Any]:
    if request.method == "GET":
        return dict(request.query_params)
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        payload = {}
    return payload if isinstance(payload, dict) else {}

def safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def safe_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): safe_payload(item) for key, item in value.items() if "secret" not in str(key).lower()}
    if isinstance(value, list):
        return [safe_payload(item) for item in value]
    if isinstance(value, tuple):
        return [safe_payload(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        text = str(value)
        if "CORE_API_KEY" in text:
            return text.replace("CORE_API_KEY", "literature API key")
        return value
    return str(value)

def safe_dashboard_payload(value: Any) -> Any:
    return safe_payload(value)

def safe_error(exc: Exception) -> str:
    return str(exc).replace("CORE_API_KEY", "literature API key")

def _cors_headers() -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Private-Network": "true",
        "Cache-Control": "no-store",
        "Cross-Origin-Resource-Policy": "cross-origin",
    }