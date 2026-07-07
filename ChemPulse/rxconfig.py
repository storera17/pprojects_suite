import os

import reflex as rx

_hot_reload_excludes = [
    "storage",
    "logs",
    "build",
    "dist",
    "Local",
]

os.environ.setdefault(
    "REFLEX_HOT_RELOAD_EXCLUDE_PATHS",
    os.pathsep.join(_hot_reload_excludes),
)

config = rx.Config(
    app_name="frontend",
    app_module_import="app",
    frontend_port=int(os.getenv("FRONTEND_PORT", "3000")),
    backend_port=int(os.getenv("BACKEND_PORT", "8000")),
    api_url=os.getenv("CHEMPULSE_API_BASE_URL") or f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8000').strip() or '8000'}",
    deploy_url=os.getenv("CHEMPULSE_DEPLOY_URL") or f"http://127.0.0.1:{os.getenv('FRONTEND_PORT', '3000').strip() or '3000'}",
    transport=os.getenv("REFLEX_TRANSPORT", "polling"),
)