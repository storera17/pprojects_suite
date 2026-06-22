from __future__ import annotations

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except Exception:  # pragma: no cover - fallback keeps the app bootable before deps install
    SentimentIntensityAnalyzer = None

_POSITIVE = {
    "beat", "beats", "growth", "gain", "gains", "up", "bullish", "strong", "upgrade", "profit",
    "record", "surge", "rally", "positive", "optimistic", "outperform", "buy", "higher",
}
_NEGATIVE = {
    "miss", "misses", "loss", "down", "bearish", "weak", "downgrade", "risk", "lawsuit",
    "fraud", "bankruptcy", "fall", "falls", "drop", "decline", "negative", "sell", "lower",
}

analyzer = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else None


def classify_sentiment_type(text: str) -> str:
    lower = (text or "").lower()
    if any(word in lower for word in ["earnings", "revenue", "eps", "guidance", "profit"]):
        return "earnings"
    if any(word in lower for word in ["fed", "inflation", "rates", "cpi", "macro", "jobs"]):
        return "macro"
    if any(word in lower for word in ["meme", "short squeeze", "diamond hands", "yolo", "wallstreetbets"]):
        return "meme"
    if any(word in lower for word in ["analyst", "upgrade", "downgrade", "target"]):
        return "analyst"
    if any(word in lower for word in ["risk", "lawsuit", "sec", "fraud", "bankruptcy"]):
        return "risk"
    return "general"


def _lexicon_score(text: str) -> float:
    words = [word.strip(".,:;!?()[]{}'\"").lower() for word in (text or "").split()]
    if not words:
        return 0.0
    positive = sum(1 for word in words if word in _POSITIVE)
    negative = sum(1 for word in words if word in _NEGATIVE)
    raw = (positive - negative) / max(4, positive + negative + 2)
    return max(-1.0, min(1.0, raw))


def score_text(text: str) -> dict:
    if analyzer:
        result = analyzer.polarity_scores(text or "")
        compound = float(result["compound"])
    else:
        compound = _lexicon_score(text or "")
    label = "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"
    return {
        "sentiment_score": compound,
        "sentiment_label": label,
        "sentiment_type": classify_sentiment_type(text or ""),
    }


def attach_sentiment(records: list[dict], text_fields: tuple[str, ...] = ("title", "selftext")) -> list[dict]:
    enriched = []
    for record in records:
        text = " ".join(str(record.get(field, "")) for field in text_fields).strip()
        enriched.append({**record, **score_text(text), "text": text})
    return enriched


def aggregate_daily_sentiment(records: list[dict]) -> dict:
    scored = [record for record in records if "sentiment_score" in record]
    if not scored:
        return {
            "daily_sentiment_score": 0.0,
            "record_count": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
        }
    scores = [float(record.get("sentiment_score", 0)) for record in scored]
    labels = [record.get("sentiment_label", "neutral") for record in scored]
    return {
        "daily_sentiment_score": round(sum(scores) / len(scores), 4),
        "record_count": len(scored),
        "positive_count": labels.count("positive"),
        "negative_count": labels.count("negative"),
        "neutral_count": labels.count("neutral"),
    }
