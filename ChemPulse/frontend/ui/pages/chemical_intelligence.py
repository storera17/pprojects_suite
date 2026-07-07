from __future__ import annotations

import reflex as rx

from frontend.ui.assets_loader import read_ui_asset


def chemical_intelligence_page() -> rx.Component:
    return rx.box(
        rx.script(_chemical_intelligence_script()),
        rx.hstack(
            rx.heading("Chemical Intelligence", size="8"),
            rx.spacer(),
            rx.link("ChemPulse OS", href="/", color="#67E8F9"),
            rx.link("Dashboard", href="/chempulse", color="#67E8F9"),
            rx.link("Journal Sentiment", href="/journal-sentiment", color="#67E8F9"),
            width="100%",
            align="center",
            margin_bottom="1rem",
        ),
        rx.text(
            "Search local literature, compare structures, triangulate reaction mechanisms, and generate explained reports from ChemPulse evidence.",
            color="#CBD5E1",
            margin_bottom="1rem",
        ),
        rx.html(_chemical_intelligence_markup()),
        padding="2rem",
    )


def _chemical_intelligence_markup() -> str:
    return read_ui_asset("chemical_intelligence_markup.html")


def _chemical_intelligence_script() -> str:
    return read_ui_asset("chemical_intelligence_script.js")
