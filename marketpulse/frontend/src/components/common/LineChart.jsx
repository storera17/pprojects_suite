import { ensureArray } from "../../utils/arrays.js";
import { formatNumber } from "../../utils/formatters.js";
import { EmptyState } from "./EmptyState.jsx";

export function LineChart({
  rows,
  valueKey = "close",
  labelKey = "date",
  label = "chart",
  height = 240,
}) {
  const points = ensureArray(rows)
    .filter((row) => Number.isFinite(Number(row?.[valueKey])))
    .slice(-80);

  if (points.length < 2) {
    return <EmptyState title="Not enough chart rows">Need at least two stored rows for this graph.</EmptyState>;
  }

  const width = 900;
  const padding = 36;
  const values = points.map((row) => Number(row[valueKey]));
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = Math.max(0.000001, maxValue - minValue);
  const chartPoints = points.map((row, index) => ({
    x: padding + (index / Math.max(1, points.length - 1)) * (width - padding * 2),
    y: height - padding - ((Number(row[valueKey]) - minValue) / range) * (height - padding * 2),
    label: String(row[labelKey] || index),
    value: Number(row[valueKey]),
  }));
  const polylinePoints = chartPoints.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");

  return (
    <div className="chart-shell">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
        <line x1={padding} x2={width - padding} y1={height - padding} y2={height - padding} className="chart-axis" />
        <line x1={padding} x2={padding} y1={padding} y2={height - padding} className="chart-axis" />
        <polyline points={polylinePoints} className="chart-line" />
        {chartPoints.map((point, index) =>
          index % Math.ceil(chartPoints.length / 10) === 0 || index === chartPoints.length - 1 ? (
            <circle key={`${point.label}-${index}`} cx={point.x} cy={point.y} r="3.5" className="chart-dot">
              <title>{`${point.label}: ${formatNumber(point.value, 4)}`}</title>
            </circle>
          ) : null,
        )}
      </svg>
      <div className="chart-meta">
        <span>{points.length} rows</span>
        <span>low {formatNumber(minValue, 3)}</span>
        <span>high {formatNumber(maxValue, 3)}</span>
      </div>
    </div>
  );
}
