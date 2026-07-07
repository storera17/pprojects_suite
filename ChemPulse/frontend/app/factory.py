from __future__ import annotations

import reflex as rx

from frontend.app.pages import register_pages
from frontend.app.routes import register_api_routes
from frontend.ui.global_css import GLOBAL_CSS
from frontend.ui.theme import app_theme


APP_STYLE = {
    "background": "radial-gradient(circle at top left, #0f172a 0%, #09090b 45%, #020617 100%)",
    "color": "#E5E7EB",
    "min_height": "100vh",
}


def create_app() -> rx.App:
    app = rx.App(
        theme=app_theme,
        style=APP_STYLE,
        head_components=[rx.html(f"<style>{GLOBAL_CSS}</style>")],
    )
    register_pages(app)
    register_api_routes(app)
    return app
