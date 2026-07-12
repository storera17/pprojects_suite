import os

import reflex as rx

_hot_reload_excludes = [
    "storage",
    "logs",
    "build",
    "dist",
]

# Only pass excludes that exist: reflex's get_reload_paths() calls path.samefile(exclude),
# which raises FileNotFoundError on a missing exclude target and kills the granian backend
# at boot (the frontend keeps running, so it looks like a silent dead backend). Join with
# ":" — what reflex splits on; os.pathsep is ";" on Windows and would be read as one path.
os.environ.setdefault(
    "REFLEX_HOT_RELOAD_EXCLUDE_PATHS",
    ":".join(d for d in _hot_reload_excludes if os.path.isdir(d)),
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