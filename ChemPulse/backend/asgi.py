from __future__ import annotations

import os

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from backend.api.route_map import all_routes


def create_backend_app() -> Starlette:
    routes = [Route(path, handler, methods=methods) for path, handler, methods in all_routes()]
    app = Starlette(debug=False, routes=routes)

    allowed_origins = [
        origin.strip()
        for origin in os.getenv("CHEMPULSE_CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.route("/healthz", methods=["GET"])
    async def healthcheck(_request):
        return JSONResponse({"ok": True, "service": "chempulse-backend"})

    return app


app = create_backend_app()
