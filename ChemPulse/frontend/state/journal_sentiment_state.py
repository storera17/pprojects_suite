from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import reflex as rx

from backend.core.palette_catalog import DEFAULT_PALETTE_KEY, normalize_palette_key
from backend.services.journal_sentiment_service import JournalSentimentService


class JournalSentimentState(rx.State):
    selected_palette: str = rx.LocalStorage(DEFAULT_PALETTE_KEY,
                                            name="chempulse.palette",
                                            sync=True)
    selected_journal: str = ""
    journals: list[str] = []
    metrics: dict[str, Any] = {
        "article_count": 0,
        "average_score": 0.0,
        "last_updated": "Never",
        "has_data": False,
        "empty_message": "No sentiment data is available.",
    }

    @rx.event
    def initialize(self):
        analysis = JournalSentimentService.analyze(self.selected_journal)
        self._apply_analysis(analysis)

    @rx.event
    def set_selected_journal(self, value: str):
        self.selected_journal = value
        self._apply_analysis(JournalSentimentService.analyze(value))
    
    @rx.event
    def set_palette(self, value: str):
        self.selected_palette = normalize_palette_key(value)
        
    def _apply_analysis(self, analysis: dict[str, Any]):
        self.selected_journal = analysis.get("selected_journal", "")
        self.journals = analysis.get("journals", [])
        self.metrics = {
            "article_count": analysis.get("article_count", 0),
            "average_score": analysis.get("average_score", 0.0),
            "last_updated": analysis.get("last_updated", "Never"),
            "has_data": analysis.get("has_data", False),
            "empty_message": analysis.get("empty_message", ""),
        }

    @rx.var
    def sentiment_figure(self) -> go.Figure:
        return JournalSentimentService.figure(self.selected_journal)

    @rx.var
    def palette_key(self) -> str:
        return normalize_palette_key(self.selected_palette)
    
    @rx.var
    def palette_class(self) -> str:
        return f"cp-theme-{self.palette_key}"