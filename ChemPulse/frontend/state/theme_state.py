from __future__ import annotations

import reflex as rx

from backend.core.palette_catalog import DEFAULT_PALETTE_KEY, normalize_palette_key


class ThemeState(rx.State):
    # Persist and expose the currently selected ChemPulse UI palette.

    selected_palette: str = rx.LocalStorage(DEFAULT_PALETTE_KEY, name="chempulse.palette", sync=True)

    @rx.event
    def set_palette(self, value: str):
        self.selected_palette = normalize_palette_key(value)

    @rx.var
    def palette_key(self) -> str:
        return normalize_palette_key(self.selected_palette)

    @rx.var
    def palette_class(self) -> str:
        return f"cp-theme-{self.palette_key}"