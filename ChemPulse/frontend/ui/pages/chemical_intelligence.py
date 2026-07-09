from __future__ import annotations

import reflex as rx

from frontend.state.theme_state import ThemeState
from frontend.ui.assets_loader import read_ui_asset
from frontend.ui.shell import shell_link, status_pill, workspace_shell


def chemical_intelligence_page() -> rx.Component:
    return workspace_shell(
        active_nav="search",
        brand="Chemical Intelligence",
        title="Chemical Intelligence",
        description="Search local literature, compare structures, explore mechanisms, generate reports, and stage source pricing without leaving the current workspace.",
        theme_class=ThemeState.palette_class,
        content=rx.box(
            rx.script(_chemical_intelligence_script()),
            rx.html(_chemical_intelligence_markup()),
        ),
        search_slot=rx.input(
            placeholder="Search workspace...",
            width="100%",
            class_name="cp-search-shell",
        ),
        topbar_actions=[
            shell_link("ChemPulse OS", "/"),
            shell_link("Dashboard", "/chempulse"),
            shell_link("Journal Sentiment", "/journal-sentiment"),
            status_pill("Core interactive", tone="live"),
        ],
        status_text="Research ready",
        status_tone="live",
    )


def _chemical_intelligence_markup() -> str:
    return read_ui_asset("chemical_intelligence_markup.html")


def _chemical_intelligence_script() -> str:
    return read_ui_asset("chemical_intelligence_script.js")
