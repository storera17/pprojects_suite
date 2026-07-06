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