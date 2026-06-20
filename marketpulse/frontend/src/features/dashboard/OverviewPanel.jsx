import { MetricCard } from "../../components/common/MetricCard.jsx";
import { formatCurrency, formatSignedNumber, titleCase } from "../../utils/formatters.js";

export function OverviewPanel({ ticker, summary, dbSummary }) {
  return (
    <section className="panel wide overview-panel">
      <div>
        <p className="eyebrow">{ticker} workspace</p>
        <h2>Executive Overview</h2>
        <p>{summary.executive_takeaway || "Refresh this ticker to build a local overview from SQLite-backed provider data."}</p>
      </div>

      <div className="metrics-grid">
        <MetricCard
          label="Latest Price"
          value={formatCurrency(summary.latest_price)}
          detail={summary.latest_price_provider || "no provider"}
          accent="blue"
        />
        <MetricCard
          label="Sentiment"
          value={titleCase(summary.sentiment_label || "unknown")}
          detail={`${summary.sentiment_items || 0} relevant scored rows | ${formatSignedNumber(summary.sentiment_avg)}`}
          accent="green"
        />
        <MetricCard
          label="Market News"
          value={summary.ticker_relevant_news_count ?? 0}
          detail={`${summary.news_count ?? 0} stored | ${summary.high_relevance_news_count ?? 0} high relevance`}
          accent="gold"
        />
        <MetricCard
          label="Local DB Rows"
          value={dbSummary.total_records ?? "n/a"}
          detail="SQLite records available"
          accent="purple"
        />
      </div>
    </section>
  );
}
