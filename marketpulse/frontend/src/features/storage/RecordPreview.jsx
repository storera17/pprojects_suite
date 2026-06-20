import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";
import { ensureArray } from "../../utils/arrays.js";
import { formatNumber, formatSignedNumber, formatTimestamp, titleCase } from "../../utils/formatters.js";

export function RecordPreview({ rows }) {
  const items = ensureArray(rows);

  if (!items.length) {
    return <EmptyState title="No stored rows match these filters">Try a broader day range or clear the category/provider filters.</EmptyState>;
  }

  return (
    <div className="storage-record-list">
      {items.map((row) => {
        const title = row.title || row.summary || row.url || `${titleCase(row.category)} record`;
        const facts = [
          row.event_date ? `event ${row.event_date}` : null,
          row.created_at ? `stored ${formatTimestamp(row.created_at)}` : null,
          Number.isFinite(Number(row.value_primary)) ? `primary ${formatNumber(row.value_primary, 4)}` : null,
          Number.isFinite(Number(row.value_secondary)) ? `secondary ${formatNumber(row.value_secondary, 4)}` : null,
          Number.isFinite(Number(row.sentiment_score)) ? `sentiment ${formatSignedNumber(row.sentiment_score, 3)}` : null,
        ].filter(Boolean);

        return (
          <article className="storage-record-card" key={row.id || `${row.provider}-${row.category}-${row.created_at}-${title}`}>
            <div className="storage-record-top">
              <div>
                <strong>{title}</strong>
                <div className="storage-record-meta">
                  <span>{titleCase(row.provider || "unknown")}</span>
                  <span>{titleCase(row.category || "unknown")}</span>
                  <span>{row.symbol || "market-wide"}</span>
                  <span>{row.period || "raw"}</span>
                </div>
              </div>
              <Badge value={row.category || "record"} />
            </div>
            {row.summary && row.summary !== row.title ? <p>{row.summary}</p> : null}
            <div className="storage-record-stats">
              {facts.map((fact) => (
                <span key={fact}>{fact}</span>
              ))}
            </div>
            {row.url ? (
              <footer>
                <a href={row.url} target="_blank" rel="noreferrer">
                  Open source
                </a>
              </footer>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}
