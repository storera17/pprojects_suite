from __future__ import annotations

import reflex as rx


def kpi_card(title: str,
             value, 
             accent: str = "var(--cp-accent-2)",
             live_id: str = "") -> rx.Component:
    return rx.box(
        rx.text(
            title,
            size="2",
            color="var(--cp-text-soft)",
            text_transform="uppercase",
            letter_spacing="0.08em",
        ),
        rx.heading(value, 
                   size="7", 
                   color="var(--cp-text)", 
                   id=live_id),
        class_name="bento-card kpi-card",
        box_shadow=f"0 0 0 1px rgba(255,255,255,0.02), 0 12px 40px rgba(0,0,0,0.28), 0 0 24px {accent}",
        grid_column="span 3",
        min_height="140px",
    )
    