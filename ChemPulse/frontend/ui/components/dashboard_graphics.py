from __future__ import annotations

import reflex as rx


def dashboard_graphics(
    journal_publication_figure,
    publication_timeline_figure,
    scaffold_publication_figure,
    source_diversity_figure,
    summary_cards,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("Publication Analytics", 
                           size="6", 
                           color="var(--cp-text)"),
                rx.spacer(),
                rx.badge("Journal-first scoring", 
                         color_scheme="cyan"),
                width="100%",
            ),
            rx.grid(
                rx.foreach(
                    summary_cards,
                    lambda item: rx.box(
                        rx.text(item["label"], 
                                color="var(--cp-text-soft)", 
                                size="2"),
                        rx.heading(item["value"], 
                                   color="var(--cp-text)", 
                                   size="5"),
                        rx.text(item["detail"], 
                                color="var(--cp-text-muted)", 
                                size="1"),
                        padding="0.75rem",
                        border_radius="8px",
                        background="var(--cp-bg-panel-soft)",
                        border="1px solid var(--cp-border)",
                    ),
                ),
                columns="repeat(4, 1fr)",
                gap="0.75rem",
                width="100%",
            ),
            rx.grid(
                _plot(journal_publication_figure),
                _plot(publication_timeline_figure),
                _plot(scaffold_publication_figure),
                _plot(source_diversity_figure),
                columns="repeat(2, minmax(0, 1fr))",
                gap="0.85rem",
                width="100%",
            ),
            align="stretch",
            spacing="3",
        ),
        class_name="bento-card",
        grid_column="span 12",
        min_height="640px",
    )


def _plot(figure) -> rx.Component:
    return rx.box(
        rx.plotly(data=figure, 
                  width="100%", 
                  height="100%"),
        height="310px",
        border_radius="8px",
        background="var(--c-plot-bg)",
        border="1px solid var(--cp-border)",
        overflow="hidden",
    )


