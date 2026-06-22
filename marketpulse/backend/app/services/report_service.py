from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.reports_repository import save_daily_report
from app.services.dashboard_service import build_dashboard


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def build_daily_report(ticker: str, period: str = "daily") -> dict:
    symbol = ticker.upper()
    dashboard = build_dashboard(symbol, period)
    summary = dashboard.get("summary", {})
    topics = dashboard.get("topics", [])[:6]
    providers = dashboard.get("provider_statuses", [])
    news = dashboard.get("news", [])[:10]

    sections = [
        {
            "title": "Executive Summary",
            "lines": [
                summary.get("executive_takeaway") or "No executive takeaway is available yet.",
                f"Sentiment: {summary.get('sentiment_label') or 'unknown'} ({summary.get('sentiment_avg')}).",
                f"Latest stored price: {summary.get('latest_price')} from {summary.get('latest_price_provider') or 'no provider yet'}.",
            ],
        },
        {
            "title": "Data Coverage",
            "lines": [
                f"Price rows: {summary.get('price_points')}",
                f"News/search rows: {summary.get('news_count')} ({summary.get('high_relevance_news_count')} high-relevance)",
                f"Macro rows: {summary.get('macro_points')}",
                f"Crypto rows: {summary.get('crypto_points')}",
                f"FX rows: {summary.get('fx_points')}",
            ],
        },
        {
            "title": "Provider Health and Cache",
            "lines": [f"{provider.get('provider')}: {provider.get('status')} - {provider.get('message') or 'No message'}" for provider in providers[:15]] or ["No provider refreshes have been recorded yet."],
        },
        {
            "title": "Topic Clusters",
            "lines": [f"{topic.get('label')}: {', '.join(topic.get('keywords', [])[:8])}" for topic in topics] or ["No topic clusters are stored yet."],
        },
        {
            "title": "Top Market-Relevant Headlines",
            "lines": [f"[{item.get('market_relevance', 'unscored')}] {item.get('title')}" for item in news] or ["No news/search items are stored yet."],
        },
        {
            "title": "Risks and Gaps",
            "lines": [
                "Dashboard endpoints read SQLite only; refresh endpoints are responsible for provider calls.",
                "When providers fail or hit rate limits, stale SQLite cache is used when available.",
                "Crypto/FX panels remain sparse until global providers are refreshed.",
            ],
        },
    ]

    report_lines = [f"Daily MarketPulse report for {symbol} ({period})"]
    for section in sections:
        report_lines.extend(["", section["title"]])
        report_lines.extend([f"- {line}" for line in section["lines"]])

    return {
        "status": "ok",
        "ticker": symbol,
        "period": period,
        "report": "\n".join(report_lines),
        "sections": sections,
        "dashboard": dashboard,
    }


def build_watchlist_brief(tickers: list[str], period: str = "daily") -> dict:
    clean = [ticker.upper() for ticker in (tickers or []) if ticker]
    report_date = _today()
    reports = [build_daily_report(ticker, period) for ticker in clean]

    lines = [f"MarketPulse Daily Brief - {report_date} ({period})", ""]
    if not reports:
        lines.append("No tickers in the watchlist to brief on yet.")
    for report in reports:
        summary = report.get("dashboard", {}).get("summary", {})
        change = summary.get("daily_change") or {}
        if change.get("available"):
            move = f"{change.get('change')} ({change.get('change_percent')}%) {change.get('direction')}"
        else:
            move = "no daily move available"
        lines.append(f"## {report['ticker']}")
        lines.append(summary.get("executive_takeaway") or "No takeaway available yet.")
        lines.append(
            f"Snapshot: price {summary.get('latest_price')} ({move}); "
            f"sentiment {summary.get('sentiment_label')} ({summary.get('sentiment_avg')}); "
            f"{summary.get('ticker_relevant_news_count', 0)} relevant news rows; "
            f"readiness {report.get('dashboard', {}).get('quality', {}).get('status')}."
        )
        lines.append("")

    return {
        "status": "ok",
        "scope": "watchlist",
        "period": period,
        "report_date": report_date,
        "tickers": [report["ticker"] for report in reports],
        "report": "\n".join(lines).strip(),
        "reports": reports,
    }


def persist_daily_brief(brief: dict, run_id: int | None = None) -> dict:
    report_date = brief.get("report_date") or _today()
    period = brief.get("period") or "daily"
    ticker_report_ids: list[int] = []
    for report in brief.get("reports", []):
        ticker_report_ids.append(
            save_daily_report(
                report_date=report_date,
                scope="ticker",
                ticker=report["ticker"],
                period=report.get("period") or period,
                title=f"{report['ticker']} daily report",
                report_text=report["report"],
                raw_json={"sections": report.get("sections", [])},
                run_id=run_id,
            )
        )
    brief_id = save_daily_report(
        report_date=report_date,
        scope="watchlist",
        ticker=None,
        period=period,
        title=f"Watchlist daily brief - {report_date}",
        report_text=brief["report"],
        raw_json={"tickers": brief.get("tickers", [])},
        run_id=run_id,
    )
    return {"brief_id": brief_id, "ticker_report_ids": ticker_report_ids, "report_date": report_date, "tickers": brief.get("tickers", [])}
