import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";
import { LineChart } from "../../components/common/LineChart.jsx";
import { ensureArray } from "../../utils/arrays.js";

function TopicClusterList({ topics }) {
  const items = ensureArray(topics).slice(0, 10);
  if (!items.length) {
    return <EmptyState title="No topic clusters yet">Refresh news/search providers to create topic clusters.</EmptyState>;
  }
  return (
    <div className="topic-grid">
      {items.map((topic, index) => (
        <article className="topic-pill" key={topic.id || index}>
          <span>{topic.source || "local"}</span>
          <strong>{topic.label || "Untitled cluster"}</strong>
          <small>{ensureArray(topic.keywords).slice(0, 10).join(", ")}</small>
        </article>
      ))}
    </div>
  );
}

function SentimentTimeline({ rows }) {
  const items = ensureArray(rows).slice(-20);
  if (!items.length) {
    return <p className="muted small">No sentiment timeline buckets are available yet.</p>;
  }
  return (
    <div className="sentiment-timeline">
      {items.map((row, index) => (
        <span
          key={`${row.date}-${index}`}
          className={`sentiment-point ${row.label || "neutral"}`}
          title={`${row.date}: ${row.label} (${row.sentiment}) | ${row.count} item(s)`}
        >
          {row.date}
        </span>
      ))}
    </div>
  );
}

export function SentimentPanel({
  ticker,
  sentimentSeries,
  sentimentTimeline,
  topics,
  sentimentLabel,
  sentimentAvailable,
}) {
  return (
    <section className="dashboard-grid one">
      <div className="panel wide">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Text analytics</p>
            <h2>{ticker} Sentiment</h2>
          </div>
          <Badge value={sentimentLabel || "unknown"} />
        </div>
        <LineChart rows={sentimentSeries} valueKey="sentiment" label={`${ticker} sentiment`} />
        <SentimentTimeline rows={sentimentTimeline} />
        {!sentimentAvailable ? (
          <p className="muted small">
            Sentiment is shown only when ticker-relevant English news/search text exists.
          </p>
        ) : null}
      </div>

      <div className="panel wide">
        <h2>Topic Drivers</h2>
        <TopicClusterList topics={topics} />
      </div>
    </section>
  );
}
