import { ensureArray } from "../../utils/arrays.js";
import { formatNumber } from "../../utils/formatters.js";
import { EmptyState } from "./EmptyState.jsx";

export function BarChart({ rows, valueKey = "value", labelKey = "symbol", label = "bar chart" }) {
  const items = ensureArray(rows)
    .filter((row) => Number.isFinite(Number(row?.[valueKey])))
    .slice(-30);

  if (!items.length) {
    return <EmptyState title="No rows stored">Run Refresh Watchlist to populate this graph.</EmptyState>;
  }

  const maxMagnitude = Math.max(1, ...items.map((row) => Math.abs(Number(row[valueKey]))));

  return (
    <div className="bar-chart" aria-label={label}>
      {items.map((row, index) => {
        const numeric = Number(row[valueKey]);
        const height = Math.max(8, Math.round((Math.abs(numeric) / maxMagnitude) * 170));
        const textLabel = String(row[labelKey] || row.title || row.symbol || index);

        return (
          <div className="bar-cell" key={`${textLabel}-${index}`} title={`${textLabel}: ${formatNumber(numeric, 4)}`}>
            <div className="bar" style={{ height }} />
            <small>{textLabel.slice(0, 8)}</small>
          </div>
        );
      })}
    </div>
  );
}
