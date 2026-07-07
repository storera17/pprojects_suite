from __future__ import annotations

from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=None)
def read_ui_asset(filename: str) -> str:
    return resources.files("frontend.ui.assets").joinpath(filename).read_text(encoding="utf-8")
