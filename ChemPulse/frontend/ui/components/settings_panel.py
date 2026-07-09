from __future__ import annotations

import reflex as rx

from backend.core.palette_catalog import PALETTE_OPTIONS
from frontend.state.theme_state import ThemeState
from frontend.ui.shell import shell_panel, status_pill


def theme_settings_panel() -> rx.Component:
    option_cards: list[rx.Component] = []
    for option in PALETTE_OPTIONS:
        option_cards.append(_palette_option(option))

    body = rx.vstack(
        rx.hstack(
            rx.text("Theme Palette", class_name="cp-card-label"),
            rx.spacer(),
            status_pill("Stored locally", tone="neutral"),
            width="100%",
            align="center",
        ),
        rx.text(
            "Choose between the research-derived Default palette and three alternate ChemPulse visual systems. The selection persists locally across routes.",
            class_name="cp-card-detail",
        ),
        rx.grid(
            *option_cards,
            columns=rx.breakpoints(initial="1", md="2"),
            gap="0.85rem",
            width="100%",
            class_name="cp-settings-grid",
        ),
        align="stretch",
        spacing="3",
    )
    return shell_panel(
        "Interface Settings",
        body,
        eyebrow="Settings",
        footer=rx.text("Default is derived from your chemistry tables, slide annotations, and working research materials.", class_name="cp-inline-muted"),
    )


def _palette_option(option: dict[str, object]) -> rx.Component:
    key = str(option["key"])
    preview = tuple(str(color) for color in option["preview"])
    label = str(option["label"])
    description = str(option["description"])
    selected = ThemeState.palette_key == key
    return rx.button(
        rx.vstack(
            rx.hstack(
                rx.text(label, class_name="cp-theme-option-title"),
                rx.spacer(),
                rx.cond(selected, status_pill("Selected", tone="live"), status_pill("Available", tone="neutral")),
                width="100%",
                align="center",
            ),
            rx.text(description, class_name="cp-card-detail"),
            rx.hstack(
                *[
                    rx.box(
                        class_name="cp-theme-swatch",
                        background=color,
                    )
                    for color in preview
                ],
                class_name="cp-theme-swatch-row",
                width="100%",
                align="center",
                spacing="2",
            ),
            align="stretch",
            spacing="3",
        ),
        on_click=lambda theme_key=key: ThemeState.set_palette(theme_key),
        variant="ghost",
        width="100%",
        height="100%",
        padding="0",
        class_name=rx.cond(selected, "cp-theme-option-button cp-theme-option-button-selected", "cp-theme-option-button"),
    )
