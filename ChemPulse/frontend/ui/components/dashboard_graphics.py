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
                rx.heading("Publication Analytics", size="6", color="white"),
                rx.spacer(),
                rx.badge("Journal-first scoring", color_scheme="cyan"),
                width="100%",
            ),
            rx.grid(
                rx.foreach(
                    summary_cards,
                    lambda item: rx.box(
                        rx.text(item["label"], color="#94A3B8", size="2"),
                        rx.heading(item["value"], color="white", size="5"),
                        rx.text(item["detail"], color="#64748B", size="1"),
                        padding="0.75rem",
                        border_radius="8px",
                        background="rgba(255,255,255,0.05)",
                        border="1px solid rgba(255,255,255,0.08)",
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
        rx.plotly(data=figure, width="100%", height="100%"),
        height="310px",
        border_radius="8px",
        background="rgba(15,23,42,0.58)",
        border="1px solid rgba(148,163,184,0.14)",
        overflow="hidden",
    )


