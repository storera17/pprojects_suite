from __future__ import annotations

import reflex as rx

from backend.api.route_map import chemical_intelligence_routes, dashboard_routes, status_routes


def register_api_routes(app: rx.App) -> None:
    for route, handler, methods in status_routes():
        app._api.add_route(route, handler, methods=methods)

    for route, handler, methods in dashboard_routes():
        app._api.add_route(route, handler, methods=methods)
        app._api.add_route(f"/chempulse{route}", handler, methods=methods)

    for route, handler, methods in chemical_intelligence_routes():
        app._api.add_route(route, handler, methods=methods)
        app._api.add_route(f"/chempulse{route}", handler, methods=methods)
