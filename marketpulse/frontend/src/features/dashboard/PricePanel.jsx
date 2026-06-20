import { BarChart } from "../../components/common/BarChart.jsx";
import { LineChart } from "../../components/common/LineChart.jsx";
import { RANGE_OPTIONS } from "../../constants/periods.js";
import { formatCurrency, formatPercent, formatSignedNumber } from "../../utils/formatters.js";

function ChangeBox({ change }) {
  const available = Boolean(change?.available);
  return (
    <section className={`daily-change-box ${available ? change.direction || "flat" : "missing"}`}>
      <span>Daily Change</span>
      <strong>
        {available
          ? `${formatSignedNumber(change.change, 2)} (${formatPercent(change.change_percent, 2)})`
          : "Unavailable"}
      </strong>
      <small>
        {available
          ? `${change.previous_date} to ${change.latest_date} | ${formatCurrency(change.previous_close)} to ${formatCurrency(change.latest_close)} | ${change.provider || "stored price"}`
          : change?.message || "Need at least two stored daily closes."}
      </small>
    </section>
  );
}

function RangeTabs({ value, onChange }) {
  return (
    <div className="range-tabs" aria-label="Price graph range">
      {RANGE_OPTIONS.map(([range, label]) => (
        <button key={range} className={value === range ? "active" : ""} onClick={() => onChange(range)}>
          {label}
        </button>
      ))}
    </div>
  );
}

export function PricePanel({
  ticker,
  range,
  onRangeChange,
  priceRows,
  volumeRows,
  dailyChange,
  volumeAvailable,
}) {
  return (
    <section className="dashboard-grid one">
      <ChangeBox change={dailyChange} />

      <div className="panel wide">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Stored prices</p>
            <h2>{ticker} Price Action</h2>
          </div>
          <span>{priceRows.length} rows</span>
        </div>
        <RangeTabs value={range} onChange={onRangeChange} />
        <LineChart rows={priceRows} valueKey="close" label={`${ticker} ${range} price action`} />
      </div>

      <div className="panel wide">
        <div className="panel-heading">
          <h2>Volume History</h2>
          <span>{volumeRows.length} rows</span>
        </div>
        <BarChart rows={volumeRows} valueKey="value" labelKey="date" label={`${ticker} volume`} />
        {!volumeAvailable ? (
          <p className="muted small">
            Volume is unavailable for this ticker/provider combination. The workspace remains valid
            with price or quote coverage.
          </p>
        ) : null}
      </div>
    </section>
  );
}
