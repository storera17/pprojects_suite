from __future__ import annotations

import reflex as rx


def selection_panel(
    selection_summary,
    selected_scaffold,
    search_query,
    top_scaffold_label,
    selected_evidence_count,
    selected_funding_label,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Active Context", size="6", color="white"),
            rx.vstack(
                rx.text("Selection", color="#94A3B8", size="2"),
                rx.text(selection_summary, color="#E2E8F0", weight="bold"),
                align="start",
                spacing="1",
            ),
            rx.vstack(
                rx.text("Scaffold Focus", color="#94A3B8", size="2"),
                rx.text(
                    rx.cond(selected_scaffold != "", selected_scaffold, top_scaffold_label),
                    color="#67E8F9",
                    weight="bold",
                ),
                align="start",
                spacing="1",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Evidence", color="#94A3B8", size="2"),
                    rx.text(selected_evidence_count.to_string(), " publications", color="#86EFAC", weight="bold"),
                    align="start",
                    spacing="1",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("Funding Enrichment", color="#94A3B8", size="2"),
                    rx.text(selected_funding_label, color="#86EFAC", weight="bold"),
                    align="end",
                    spacing="1",
                ),
                width="100%",
            ),
            rx.vstack(
                rx.text("Search", color="#94A3B8", size="2"),
                rx.text(
                    rx.cond(search_query != "", search_query, "No active search"),
                    color="#CBD5E1",
                ),
                align="start",
                spacing="1",
            ),
            align="stretch",
            spacing="4",
        ),
        class_name="bento-card",
        grid_column="span 4",
        min_height="250px",
    )


