import { Badge } from "../../components/common/Badge.jsx";
import { CoverageList } from "./CoverageList.jsx";
import { RecordPreview } from "./RecordPreview.jsx";
import { formatTimestamp, titleCase } from "../../utils/formatters.js";

export function TickerStoragePanel({
  ticker,
  storageSymbol,
  onStorageSymbolChange,
  availability,
  recordsPayload,
  loading,
  error,
  filters,
  onFilterChange,
  onInspect,
  onUseActiveTicker,
}) {
  const categories = Object.keys(availability.categories || {}).sort();
  const providers = Object.keys(availability.providers || {}).sort();
  const hasData = Boolean(availability.has_data);
  const recordCount = recordsPayload.count ?? (recordsPayload.records || []).length;

  return (
    <section className="panel wide storage-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">SQLite ticker storage</p>
          <h2>Stored Data Inspector</h2>
        </div>
        <Badge value={loading ? "loading" : hasData ? "cached" : "missing"} />
      </div>

      <p className="muted">
        Check local SQLite coverage before forcing another provider refresh. Inspect any ticker,
        narrow to a provider/category slice, and preview recent stored rows.
      </p>

      <div className="storage-toolbar">
        <div className="storage-symbol-box">
          <label htmlFor="storage-symbol">Inspect symbol</label>
          <div className="inline-form">
            <input
              id="storage-symbol"
              value={storageSymbol}
              onChange={(event) => onStorageSymbolChange(event.target.value)}
              placeholder="Example: SPY"
            />
            <button type="button" onClick={onInspect} disabled={loading}>
              {loading ? "Checking..." : "Inspect"}
            </button>
          </div>
        </div>

        <button type="button" className="ghost" onClick={onUseActiveTicker}>
          Use Active {ticker}
        </button>
      </div>

      {error ? <div className="notice">{error}</div> : null}

      <div className="storage-summary-grid">
        <div>
          <span>SQLite presence</span>
          <b>{hasData ? "stored" : "missing"}</b>
        </div>
        <div>
          <span>Total rows</span>
          <b>{availability.record_count ?? 0}</b>
        </div>
        <div>
          <span>Latest event</span>
          <b>{availability.latest_event_date || "not recorded"}</b>
        </div>
        <div>
          <span>Last stored</span>
          <b>{formatTimestamp(availability.latest_created_at)}</b>
        </div>
      </div>

      <p className="microcopy">{availability.message || "Inspect a ticker to see what is already persisted locally."}</p>

      <div className="analytics-grid two">
        <CoverageList title="Category coverage" rows={availability.categories} tone={hasData ? "positive" : "neutral"} />
        <CoverageList title="Provider coverage" rows={availability.providers} tone={hasData ? "configured" : "neutral"} />
      </div>

      <div className="storage-filters">
        <div>
          <label htmlFor="storage-category">Category</label>
          <select
            id="storage-category"
            value={filters.category}
            onChange={(event) => onFilterChange("category", event.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {titleCase(category)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="storage-provider">Provider</label>
          <select
            id="storage-provider"
            value={filters.provider}
            onChange={(event) => onFilterChange("provider", event.target.value)}
          >
            <option value="">All providers</option>
            {providers.map((provider) => (
              <option key={provider} value={provider}>
                {titleCase(provider)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="storage-days">Days</label>
          <select
            id="storage-days"
            value={String(filters.days)}
            onChange={(event) => onFilterChange("days", Number(event.target.value))}
          >
            {[30, 90, 365, 1825, 3650].map((days) => (
              <option key={days} value={days}>
                {days} days
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="storage-limit">Preview rows</label>
          <select
            id="storage-limit"
            value={String(filters.limit)}
            onChange={(event) => onFilterChange("limit", Number(event.target.value))}
          >
            {[10, 25, 50, 100].map((limit) => (
              <option key={limit} value={limit}>
                {limit} rows
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="panel-heading storage-records-head">
        <div>
          <h3>Recent Stored Rows</h3>
          <p className="muted small">
            Showing {recordCount || 0} row{recordCount === 1 ? "" : "s"} for {storageSymbol || ticker}.
          </p>
        </div>
        <button type="button" className="ghost" onClick={onInspect} disabled={loading}>
          Reload Records
        </button>
      </div>

      <RecordPreview rows={recordsPayload.records} />
    </section>
  );
}
