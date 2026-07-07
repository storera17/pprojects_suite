from __future__ import annotations

import reflex as rx


def kpi_card(title: str, value, accent: str = "#22d3ee", live_id: str = "") -> rx.Component:
    return rx.box(
        rx.text(
            title,
            size="2",
            color="#94A3B8",
            text_transform="uppercase",
            letter_spacing="0.08em",
        ),
        rx.heading(value, size="7", color="white", id=live_id),
        class_name="bento-card kpi-card",
        box_shadow=f"0 0 0 1px rgba(255,255,255,0.02), 0 12px 40px rgba(0,0,0,0.28), 0 0 24px {accent}22",
        grid_column="span 3",
        min_height="140px",
    )