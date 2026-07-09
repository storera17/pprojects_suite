from __future__ import annotations

import reflex as rx


def galaxy_map(plot, 
               selection_summary, 
               on_select, on_clear) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("3D Molecular Galaxy Map", 
                           size="6", 
                           color="var(--cp-text)"),
                rx.spacer(),
                rx.badge("Linked Brushing", 
                         color_scheme="cyan"),
                width="100%",
            ),
            rx.text(
                "Every scaffold is represented as a centroid. Click or lasso to inspect connected journal publications, optional funding enrichment, and predictions.",
                color="var(--cp-text-soft)",
            ),
            rx.hstack(
                rx.text(selection_summary, 
                        color="var(--cp-link)"),
                rx.spacer(),
                rx.button("Clear selection", 
                          on_click=on_clear, 
                          variant="soft", 
                          color_scheme="gray"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.badge("Dot = scaffold", 
                         color_scheme="cyan"),
                rx.badge("Size = publications", 
                         color_scheme="green"),
                rx.badge("Color = publications", 
                         color_scheme="purple"),
                rx.badge("All labels shown", 
                         color_scheme="gray"),
                width="100%",
                wrap="wrap",
            ),
            rx.box(
                rx.text(
                    "No galaxy points available yet.",
                    color="var(--cp-text-soft)",
                    padding="1rem",
                ),
                rx.plotly(
                    data=plot,
                    on_selected=on_select,
                    on_click=on_select,
                    width="100%",
                    height="100%",
                ),
                width="100%",
                height="520px",
                border_radius="8px",
                background="linear-gradient(180deg, var(--cp-bg-elevated), var(--cp-bg-app-deep))",
                border="1px solid var(--cp-border-strong)",
                overflow="hidden",
            ),
            align="stretch",
            spacing="4",
        ),
        class_name="bento-card",
        grid_column="span 8",
        min_height="690px",
    )



