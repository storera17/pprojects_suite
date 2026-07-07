from __future__ import annotations

import reflex as rx


def funding_card(title: str, items) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(title, size="5", color="white"),
            rx.foreach(
                items,
                lambda item: rx.vstack(
                    rx.hstack(
                        rx.text(item["label"], color="#E2E8F0", weight="bold"),
                        rx.spacer(),
                        rx.text(item["value"], color="#86EFAC"),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text(item.get("share", "0%"), color="#94A3B8", size="2"),
                        rx.spacer(),
                        rx.text(f"{item.get('count', 0)} scaffolds", color="#64748B", size="2"),
                        width="100%",
                    ),
                    rx.text(item.get("funding_label", ""), color="#64748B", size="1"),
                    width="100%",
                    spacing="0",
                ),
            ),
            rx.text("No journal publication sources available yet.", color="#94A3B8", size="2"),
            align="stretch",
        ),
        class_name="bento-card",
        grid_column="span 4",
        min_height="260px",
    )