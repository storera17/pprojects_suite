from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from backend.api.responses import request_payload, safe_json_or_error
from backend.services.pricing_service import PricingService


async def pricing_compare(request: Request) -> Response:
    body = await request_payload(request)
    return safe_json_or_error(lambda: PricingService.compare(body))


async def pricing_history(request: Request) -> Response:
    body = await request_payload(request)
    return safe_json_or_error(lambda: PricingService.history(body))


async def pricing_watch(request: Request) -> Response:
    body = await request_payload(request)
    return safe_json_or_error(lambda: PricingService.watch(body))
