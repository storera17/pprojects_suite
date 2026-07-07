from __future__ import annotations

import reflex as rx

from frontend.state.journal_sentiment_state import JournalSentimentState


def journal_sentiment_page() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading("Journal Sentiment", size="8"),
            rx.spacer(),
            rx.link("ChemPulse OS", href="/", color="#67E8F9"),
            rx.link("Dashboard", href="/chempulse", color="#67E8F9"),
            width="100%",
            align="center",
            margin_bottom="1rem",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("Journal", color="#94A3B8"),
                    rx.select(
                        JournalSentimentState.journals,
                        value=JournalSentimentState.selected_journal,
                        on_change=JournalSentimentState.set_selected_journal,
                        width="360px",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.grid(
                    _metric("Articles", JournalSentimentState.metrics["article_count"].to_string()),
                    _metric("Average score", JournalSentimentState.metrics["average_score"].to_string()),
                    _metric("Last updated", JournalSentimentState.metrics["last_updated"]),
                    columns="repeat(3, 1fr)",
                    gap="0.75rem",
                    width="100%",
                ),
                rx.cond(
                    JournalSentimentState.metrics["has_data"],
                    rx.box(
                        rx.plotly(data=JournalSentimentState.sentiment_figure, width="100%", height="100%"),
                        height="430px",
                        border_radius="8px",
                        background="rgba(15,23,42,0.58)",
                        border="1px solid rgba(148,163,184,0.14)",
                        overflow="hidden",
                    ),
                    rx.box(
                        rx.text(JournalSentimentState.metrics["empty_message"], color="#CBD5E1"),
                        padding="1rem",
                        border_radius="8px",
                        background="rgba(255,255,255,0.05)",
                        border="1px solid rgba(255,255,255,0.08)",
                    ),
                ),
                align="stretch",
                spacing="4",
            ),
            class_name="bento-card",
        ),
        padding="2rem",
    )


def _metric(label: str, value) -> rx.Component:
    return rx.box(
        rx.text(label, color="#94A3B8", size="2"),
        rx.heading(value, color="white", size="5"),
        padding="0.85rem",
        border_radius="8px",
        background="rgba(255,255,255,0.05)",
        border="1px solid rgba(255,255,255,0.08)",
    )


