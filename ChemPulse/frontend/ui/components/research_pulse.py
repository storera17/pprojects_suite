from __future__ import annotations

import reflex as rx


def research_pulse_panel(items, on_refresh) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("Research Pulse", size="6", color="white"),
                rx.spacer(),
                rx.button("Refresh", on_click=on_refresh, variant="soft", color_scheme="cyan"),
                width="100%",
                align="center",
            ),
            rx.foreach(
                items,
                lambda item: rx.box(
                    rx.hstack(
                        rx.badge(item["tag"], color_scheme="cyan"),
                        rx.spacer(),
                        rx.text(item["metric"], color="#86EFAC", weight="bold"),
                        width="100%",
                        align="center",
                    ),
                    rx.text(item["title"], color="white", weight="bold"),
                    rx.text(item["body"], color="#CBD5E1"),
                    padding="0.85rem",
                    border_radius="14px",
                    background="rgba(255,255,255,0.05)",
                    border="1px solid rgba(255,255,255,0.08)",
                    width="100%",
                ),
            ),
            rx.text("Research Pulse is waiting for local scaffold and publication context.", color="#94A3B8", size="2"),
            spacing="3",
            align="stretch",
        ),
        class_name="bento-card",
        grid_column="span 8",
        min_height="280px",
    )
