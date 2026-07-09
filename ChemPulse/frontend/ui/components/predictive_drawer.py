from __future__ import annotations

import reflex as rx


def predictive_drawer(insights, 
                      selected_scaffold, 
                      selection_summary) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Predictive Lab", 
                       size="6",
                       color="var(--cp-text)"),
            rx.text(
                rx.cond(
                    selected_scaffold != "",
                    f"Focused scaffold: {selected_scaffold}",
                    selection_summary,
                ),
                color="var(--cp-text-soft)",
            ),
            rx.hstack(
                rx.badge("Evidence weighting", 
                         color_scheme="green"),
                rx.badge("Source diversity", 
                         color_scheme="cyan"),
                rx.badge("Assay labels optional", 
                         color_scheme="gray"),
                width="100%",
                wrap="wrap",
            ),
            rx.button("Run prediction", 
                      variant="soft", 
                      color_scheme="green", 
                      width="100%"),
            rx.cond(
                insights.length() == 0,
                rx.box(
                    rx.text("Select a scaffold point or Top 10 row to generate context-specific predictions.", 
                            color="var(--cp-text-muted)"),
                    padding="0.85rem",
                    border_radius="8px",
                    background="var(--cp-bg-panel-soft)",
                    border="1px solid var(--cp-border)",
                ),
            ),
            rx.foreach(
                insights,
                lambda item: rx.box(
                    rx.hstack(
                        rx.text(item["title"], 
                                weight="bold", 
                                color="var(--cp-text)"),
                        rx.spacer(),
                        rx.badge(item["confidence"], 
                                 color_scheme="purple"),
                        width="100%",
                    ),
                    rx.text(item["reason"], 
                            color="var(--cp-text-muted)"),
                    rx.hstack(
                        rx.badge(f"Publications: {item.get('precedent_count', 
                                 item.get('evidence_count', 0))}", 
                                 color_scheme="cyan"),
                        rx.badge(item.get("top_funder", 
                                          "Unknown source"), 
                                 color_scheme="green"),
                        width="100%",
                        wrap="wrap",
                    ),
                    rx.text(item.get("mechanism", ""), 
                            color="var(--cp-success)", 
                            size="2"),
                    rx.text(item.get("lab_action", ""), 
                            color="var(--cp-text)", 
                            size="2"),
                    rx.text(item.get("validation", ""), 
                            color="var(--cp-text-muted)", 
                            size="2"),
                    rx.text(item.get("limitation", ""), 
                            color="var(--cp-text-soft)", 
                            size="1"),
                    rx.link(
                        item.get("representative_doi", ""),
                        href=f"https://doi.org/{item.get('representative_doi', '')}",
                        is_external=True,
                        color="var(--cp-link)",
                    ),
                    padding="0.85rem",
                    border_radius="8px",
                    background="var(--cp-bg-panel-soft)",
                    border="1px solid var(--cp-border)",
                    width="100%",
                ),
            ),
            align="stretch",
            spacing="3",
        ),
        class_name="bento-card",
        grid_column="span 4",
        min_height="560px",
    )


