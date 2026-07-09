from __future__ import annotations

from collections.abc import Sequence

import reflex as rx

SHELL_NAV_ITEMS: tuple[dict[str, str], ...] = (
    {"key": "launcher", "label": "Home", "route": "/"},
    {"key": "dashboard", "label": "ChemPulse", "route": "/chempulse"},
    {"key": "search", "label": "Search", "route": "/chemical-intelligence"},
    {"key": "collections", "label": "Collections", "route": "/journal-sentiment"},
    {"key": "reports", "label": "Reports", "route": "/chempulse"},
    {"key": "settings", "label": "Settings", "route": "/"},
)

def workspace_shell(
    *,
    active_nav: str,
    brand: str,
    title: str,
    description: str,
    content: rx.Component,
    theme_class: str = "",
    topbar_actions: Sequence[rx.Component] | None = None,
    search_slot: rx.Component | None = None,
    status_text: str = "All systems operational",
    status_tone: str = "live",
) -> rx.Component:
    return rx.box(
        rx.hstack(
            _sidebar(active_nav=active_nav, brand=brand, status_text=status_text, status_tone=status_tone),
            rx.vstack(
                _topbar(title=title, search_slot=search_slot, topbar_actions=topbar_actions or ()),
                rx.box(
                    rx.vstack(
                        rx.text(
                            brand,
                            class_name="cp-eyebrow",
                        ),
                        rx.heading(title, size="8", class_name="cp-page-title"),
                        rx.text(description, class_name="cp-page-subtitle"),
                        content,
                        class_name="cp-page-content",
                        align="stretch",
                        spacing="4",
                    ),
                    class_name="cp-main-scroll",
                ),
                class_name="cp-main",
                align="stretch",
                spacing="0",
            ),
            class_name="cp-shell",
            align="stretch",
            spacing="0",
        ),
        class_name=f"cp-app-root {theme_class}".strip(),
    )

def shell_panel(
    title: str,
    body: rx.Component,
    *,
    eyebrow: str = "",
    badges: Sequence[rx.Component] | None = None,
    footer: rx.Component | None = None,
    class_name: str = "",
) -> rx.Component:
    body_items: list[rx.Component] = []
    if eyebrow:
        body_items.append(rx.text(eyebrow, class_name="cp-eyebrow"))
    body_items.append(
        rx.hstack(
            rx.heading(title, size="5", class_name="cp-panel-title"),
            rx.spacer(),
            *(badges or ()),
            width="100%",
            align="center",
        )
    )
    body_items.append(body)
    if footer is not None:
        body_items.append(rx.box(footer, class_name="cp-panel-footer"))
    return rx.box(
        rx.vstack(
            *body_items,
            class_name="cp-panel-stack",
            align="stretch",
            spacing="3",
        ),
        class_name=f"bento-card cp-panel {class_name}".strip(),
    )

def status_pill(label: str, *, tone: str = "neutral") -> rx.Component:
    return rx.box(
        label,
        class_name=f"cp-status-pill cp-status-pill-{tone}",
    )


def shell_link(label: str, href: str) -> rx.Component:
    return rx.link(
        label,
        href=href,
        class_name="cp-link",
        is_external=False,
    )

def metric_panel(
    title: str,
    value,
    *,
    detail: str = "",
    accent_class: str = "cp-accent-cyan",
    live_id: str = "",
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(title, class_name="cp-card-label"),
            rx.heading(value, size="7", class_name="cp-card-value", id=live_id),
            rx.cond(detail != "", rx.text(detail, class_name="cp-card-detail")),
            align="start",
            spacing="1",
        ),
        class_name=f"bento-card cp-metric-panel {accent_class}",
    )

def _topbar(title: str, search_slot: rx.Component | None, topbar_actions: Sequence[rx.Component]) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.box(class_name="cp-brand-mark"),
            rx.text(title, class_name="cp-topbar-title"),
            class_name="cp-topbar-brand",
            align="center",
            spacing="3",
        ),
        rx.spacer(),
        rx.cond(search_slot is not None, rx.box(search_slot, class_name="cp-topbar-search")),
        rx.hstack(
            *topbar_actions,
            class_name="cp-topbar-actions",
            align="center",
            spacing="3",
        ),
        class_name="cp-topbar",
        width="100%",
        align="center",
    )

def _sidebar(*, active_nav: str, brand: str, status_text: str, status_tone: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(class_name="cp-brand-mark"),
                rx.text(brand, class_name="cp-sidebar-brand"),
                width="100%",
                align="center",
                spacing="3",
            ),
            rx.vstack(
                *[_nav_link(item, active=item["key"] == active_nav) for item in SHELL_NAV_ITEMS],
                class_name="cp-sidebar-nav",
                align="stretch",
                spacing="3",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text("Status", class_name="cp-sidebar-section-title"),
                status_pill(status_text, tone=status_tone),
                align="start",
                spacing="2",
                width="100%",
            ),
            class_name="cp-sidebar",
            align="stretch",
            spacing="4",
        ),
    )

def _nav_link(item: dict[str, str], *, active: bool) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(class_name="cp-nav-glyph"),
            rx.text(item["label"], class_name="cp-nav-label"),
            class_name="cp-nav-link-inner",
            align="center",
            spacing="3",
            width="100%",
        ),
        href=item["route"],
        is_external=False,
        class_name="cp-nav-link-active" if active else "cp-nav-link",
    )
