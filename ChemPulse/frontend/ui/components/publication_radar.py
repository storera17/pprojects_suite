from __future__ import annotations

import reflex as rx


def publication_radar(
    publications,
    metrics,
    journals,
    on_refresh,
    import_path,
    on_import_path_change,
    on_import,
    import_status,
    gmail_status,
    gmail_leads,
    on_pull_gmail,
    on_import_gmail,
    on_import_all_gmail,
) -> rx.Component:
    def gmail_row(item):
        return rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text(item["title"], color="white", weight="bold"),
                    rx.hstack(
                        rx.text(item["journal"], color="#67E8F9", size="2"),
                        rx.text("|", color="#475569", size="2"),
                        rx.text(item["year"], color="#67E8F9", size="2"),
                        spacing="1",
                    ),
                    rx.text(item["authors"], color="#CBD5E1", size="2"),
                    rx.text(item["provenance_label"], color="#94A3B8", size="1"),
                    rx.text(item["subject"], color="#64748B", size="1"),
                    align="start",
                    spacing="1",
                    width="100%",
                ),
                rx.button(
                    "Import",
                    on_click=lambda: on_import_gmail(item["lead_id"]),
                    variant="soft",
                    color_scheme="green",
                    size="1",
                ),
                width="100%",
                align="start",
                gap="0.75rem",
            ),
            padding="0.75rem",
            border_radius="12px",
            background="rgba(255,255,255,0.04)",
            border="1px solid rgba(255,255,255,0.08)",
            width="100%",
        )

    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("Publication Radar", size="6", color="white"),
                rx.spacer(),
                rx.button("Refresh", on_click=on_refresh, variant="soft", color_scheme="cyan"),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.badge(metrics["last_run_status"], id="cp-publication-radar-run-status", color_scheme="cyan"),
                rx.text(metrics["last_run_delta"], id="cp-publication-radar-run-delta", color="#94A3B8"),
                rx.spacer(),
                rx.text(f"{metrics['publication_count']} publications", id="cp-publication-radar-count", color="#86EFAC", weight="bold"),
                width="100%",
                wrap="wrap",
            ),
            rx.vstack(
                rx.hstack(
                    rx.input(
                        id="cp-publication-import-input",
                        placeholder="Paste an email link, DOI, article URL, file, or folder path...",
                        value=import_path,
                        on_change=on_import_path_change,
                        width="100%",
                        bg="rgba(255,255,255,0.06)",
                        border="1px solid rgba(255,255,255,0.10)",
                    ),
                    rx.button("Import", id="cp-publication-import-button", on_click=on_import, variant="soft", color_scheme="green"),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    import_status != "",
                    rx.text(import_status, id="cp-publication-import-status", color="#CBD5E1", size="2"),
                    rx.text("Quick-import supports DOI and article URLs; batch import supports CSV, JSON, JSONL, and folders.", id="cp-publication-import-status", color="#64748B", size="2"),
                ),
                width="100%",
                align="stretch",
                spacing="2",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("Gmail quick import", color="#E2E8F0", weight="bold"),
                    rx.spacer(),
                    rx.button(
                        "Import All",
                        on_click=on_import_all_gmail,
                        variant="soft",
                        color_scheme="green",
                        size="1",
                    ),
                    rx.button("Pull Gmail Leads", on_click=on_pull_gmail, variant="soft", color_scheme="amber", size="1"),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    gmail_status != "",
                    rx.text(gmail_status, color="#CBD5E1", size="2"),
                    rx.text("Pull recent Academia recommendation links from Gmail, then import one paper or the full loaded batch into ChemPulse.", color="#64748B", size="2"),
                ),
                rx.cond(
                    gmail_leads.length() > 0,
                    rx.vstack(
                        rx.foreach(gmail_leads, gmail_row),
                        width="100%",
                        align="stretch",
                        spacing="2",
                    ),
                ),
                width="100%",
                align="stretch",
                spacing="2",
            ),
            rx.foreach(
                publications,
                lambda item: rx.box(
                    rx.hstack(
                        rx.text(item["journal"], color="#67E8F9", weight="bold"),
                        rx.spacer(),
                        rx.badge(item["relevance_level"], color_scheme="green"),
                        rx.badge(item["year"], color_scheme="purple"),
                        width="100%",
                        align="center",
                    ),
                    rx.text(item["title"], color="white", weight="bold"),
                    rx.text(item["authors"], color="#CBD5E1"),
                    rx.text(item["summary"], color="#94A3B8"),
                    rx.hstack(
                        rx.badge(item["topics"], color_scheme="gray"),
                        rx.spacer(),
                        rx.cond(
                            item["url"] != "",
                            rx.link("Open", href=item["url"], is_external=True, color="#67E8F9"),
                            rx.text(item["doi"], color="#64748B"),
                        ),
                        width="100%",
                        align="center",
                    ),
                    padding="0.85rem",
                    border_radius="14px",
                    background="rgba(255,255,255,0.05)",
                    border="1px solid rgba(255,255,255,0.08)",
                    width="100%",
                ),
            ),
            rx.box(
                rx.text("Source Mix", color="#94A3B8", size="2"),
                rx.foreach(
                    journals,
                    lambda item: rx.hstack(
                        rx.text(item["label"], color="#CBD5E1"),
                        rx.spacer(),
                        rx.badge(item["count"], color_scheme="green"),
                        width="100%",
                    ),
                ),
                rx.text("No journal source mix available yet.", color="#64748B", size="2"),
                width="100%",
            ),
            spacing="3",
            align="stretch",
        ),
        class_name="bento-card",
        grid_column="span 8",
        min_height="560px",
    )


