from __future__ import annotations

from statistics import mean
from typing import Any

import plotly.graph_objects as go

from backend.data.core_publication_repository import CorePublicationRepository


POSITIVE_TERMS = {
    "improved",
    "effective",
    "efficient",
    "stable",
    "selective",
    "potent",
    "robust",
    "novel",
    "promising",
    "successful",
    "enhanced",
    "high",
}

NEGATIVE_TERMS = {
    "toxic",
    "unstable",
    "failed",
    "poor",
    "limited",
    "degraded",
    "inactive",
    "adverse",
    "low",
    "risk",
    "inhibited",
}


class JournalSentimentService:
    @staticmethod
    def available_journals() -> list[str]:
        return CorePublicationRepository.available_journals()

    @staticmethod
    def analyze(journal: str = "") -> dict[str, Any]:
        journals = JournalSentimentService.available_journals()
        selected = journal.strip() or (journals[0] if journals else "")
        records = CorePublicationRepository.journal_publication_texts(selected) if selected else []
        points = [_score_record(record) for record in records]
        scores = [point["score"] for point in points]
        average = round(mean(scores), 3) if scores else 0.0
        return {
            "selected_journal": selected,
            "journals": journals,
            "has_data": bool(points),
            "empty_message": "" if points else "No sentiment data is available for the selected journal.",
            "article_count": len(points),
            "average_score": average,
            "last_updated": _last_updated(points),
            "points": points,
        }

    @staticmethod
    def figure(journal: str = "") -> go.Figure:
        analysis = JournalSentimentService.analyze(journal)
        points = analysis["points"]
        fig = go.Figure()
        if points:
            fig.add_trace(
                go.Scatter(
                    x=[point["label"] for point in points],
                    y=[point["score"] for point in points],
                    mode="lines+markers",
                    marker=dict(color="#22D3EE", size=7),
                    line=dict(color="#86EFAC", width=3),
                    customdata=[point["title"] for point in points],
                    hovertemplate="<b>%{customdata}</b><br>Sentiment: %{y}<extra></extra>",
                )
            )
        fig.update_layout(
            title=dict(text="Journal sentiment over article batches", font=dict(color="#E2E8F0", size=15)),
            margin=dict(l=8, r=8, b=36, t=42),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.42)",
            font=dict(color="#CBD5E1", size=11),
            height=390,
        )
        fig.update_xaxes(title="Article batch", gridcolor="rgba(148,163,184,0.14)")
        fig.update_yaxes(title="Sentiment score", range=[-1.05, 1.05], gridcolor="rgba(148,163,184,0.14)")
        return fig


def _score_record(record: dict[str, Any]) -> dict[str, Any]:
    text = f"{record.get('title', '')} {record.get('abstract', '')} {record.get('topics', '')}".lower()
    positive = sum(1 for term in POSITIVE_TERMS if term in text)
    negative = sum(1 for term in NEGATIVE_TERMS if term in text)
    total = positive + negative
    score = 0.0 if total == 0 else round((positive - negative) / total, 3)
    year = record.get("year") or "n/a"
    return {
        "core_id": record.get("core_id", ""),
        "title": record.get("title", "Untitled"),
        "journal": record.get("journal", "Unknown source"),
        "year": year,
        "label": f"{year} #{record.get('core_id', '')}",
        "score": score,
        "positive_hits": positive,
        "negative_hits": negative,
        "fetched_at": record.get("fetched_at"),
    }


def _last_updated(points: list[dict[str, Any]]) -> str:
    values = [point.get("fetched_at") for point in points if point.get("fetched_at")]
    if not values:
        return "Never"
    value = max(values)
    return value.isoformat() if hasattr(value, "isoformat") else str(value)
