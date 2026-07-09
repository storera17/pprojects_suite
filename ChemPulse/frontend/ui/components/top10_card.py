from __future__ import annotations

import reflex as rx


def top10_card(title: str, items, on_select_scaffold=None) -> rx.Component:
    def row(item):
        content = rx.box(
            rx.box(
                width=item.get("bar_width", "0%"),
                height="100%",
                background="var(--cp-progress-fill)",
                position="absolute",
                left="0",
                top="0",
            ),
            rx.hstack(
                rx.text(item["rank"], color="var(--cp-text-muted)", width="1.4rem"),
                rx.vstack(
                    rx.text(item["name"], color="var(--cp-text)", weight="bold"),
                    rx.text(item.get("journal_label", "Unknown source"), color="var(--cp-success)", size="2"),
                    rx.text(item.get("funding_label", "No funding data"), color="var(--cp-text-muted)", size="1"),
                    align="start",
                    spacing="0",
                ),
                rx.spacer(),
                rx.badge(item.get("publication_label", item["count"]), color_scheme="cyan"),
                width="100%",
                position="relative",
                z_index="1",
            ),
            width="100%",
            position="relative",
            overflow="hidden",
            border_radius="8px",
            padding="0.45rem",
        )
        if on_select_scaffold is None:
            return content
        return rx.button(
            content,
            on_click=lambda: on_select_scaffold(item["name"]),
            variant="ghost",
            width="100%",
            justify="start",
            padding="0",
            height="auto",
        )

    return rx.box(
        rx.vstack(
            rx.heading(title, size="5", color="var(--cp-text)"),
            rx.foreach(items, row),
            rx.text("No scaffold publication records available yet.", color="var(--cp-text-soft)", size="2"),
            spacing="3",
            align="stretch",
        ),
        class_name="bento-card",
        grid_column="span 4",
        min_height="360px",
    )


