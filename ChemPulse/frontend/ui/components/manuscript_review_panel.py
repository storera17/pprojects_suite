from __future__ import annotations

import reflex as rx


def manuscript_review_panel(
    summary,
    missing_citations,
    requested_experiments,
    journal_transfer_notes,
    response_checklist,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("Manuscript Review", 
                           size="6", 
                           color="var(--cp-text)"),
                rx.spacer(),
                rx.badge(summary["decision"], 
                         color_scheme="red"),
                rx.badge(summary["manuscript_id"], 
                         color_scheme="cyan"),
                width="100%",
                align="center",
            ),
            rx.text(summary["title"], 
                    color="var(--cp-texted-muted)", 
                    weight="bold"),
            rx.hstack(
                rx.badge(f"{summary['citation_count']} citations", 
                         color_scheme="purple"),
                rx.badge(f"{summary['experiment_count']} experiments", 
                         color_scheme="green"),
                rx.badge(f"{summary['transfer_count']} transfer notes",
                         color_scheme="amber"),
                rx.spacer(),
                rx.text(summary["source_label"], 
                        color="var(--cp-text-muted)", 
                        size="2"),
                width="100%",
                wrap="wrap",
            ),
            rx.grid(
                _bucket("Missing Citations", 
                        missing_citations,
                        "citation", 
                        "rationale"),
                _bucket("Requested Experiments", 
                        requested_experiments,
                        "experiment",
                        "request"),
                _bucket("Journal Transfer", 
                        journal_transfer_notes, 
                        "journal", 
                        "note"),
                columns="repeat(3, minmax(0, 1fr))",
                gap="0.65rem",
                width="100%",
                class_name="manuscript-review-buckets",
            ),
            rx.box(
                rx.text("Response Checklist", 
                        color="var(--cp-text-soft)", 
                        size="2", 
                        weight="bold"),
                rx.foreach(
                    response_checklist,
                    lambda item: rx.hstack(
                        rx.box(
                            width="14px",
                            height="14px",
                            border="1px solid var(--cp-border-strong)",
                            border_radius="3px",
                            flex_shrink="0",
                            margin_top="0.18rem",
                        ),
                        rx.text(item["task"], 
                                color="var(--cp-text)", 
                                size="2"),
                        width="100%",
                        align="start",
                    ),
                ),
                rx.text(
                    "No response checklist available yet.",
                    color="var(--cp-text-muted)",
                    size="2",
                ),
                width="100%",
            ),
            spacing="3",
            align="stretch",
        ),
        class_name="bento-card",
        grid_column="span 12",
        min_height="360px",
    )


def _bucket(title: str,
            items,
            label_key: str, 
            detail_key: str) -> rx.Component:
    return rx.box(
        rx.text(title, 
                color="var(--cp-text-soft)", 
                size="2", 
                weight="bold"),
        rx.foreach(
            items,
            lambda item: rx.box(
                rx.text(item[label_key], 
                        color="var(--cp-text)",
                        weight="bold", 
                        size="2"),
                rx.text(item[detail_key], 
                        color="var(--cp-text-muted)",
                        size="2"),
                padding="0.65rem",
                border_radius="8px",
                background="var(--cp-bg-panel-soft)",
                border="1px solid var(--cp-border)"
            ),
        ),
        width="100%",
    )
