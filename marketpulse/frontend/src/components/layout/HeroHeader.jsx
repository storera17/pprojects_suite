import { PERIOD_OPTIONS } from "../../constants/periods.js";

export function HeroHeader({
  activeTicker,
  period,
  pendingTicker,
  loading,
  validating,
  notice,
  onActiveTickerChange,
  onTickerBlur,
  onPeriodChange,
  onPendingTickerChange,
  onAddTicker,
  onReload,
  onRefreshTicker,
  onRefreshWatchlist,
}) {
  return (
    <header className="hero-pro">
      <div className="hero-main">
        <p className="eyebrow">Local-first financial intelligence</p>
        <h1>MarketPulse Local Pro</h1>
        <p className="hero-text">
          A portfolio-ready market intelligence dashboard with cache-first provider refresh, SQLite
          persistence, ticker workspaces, sentiment analytics, crypto/FX coverage, and a local
          analyst workflow.
        </p>

        <div className="hero-actions">
          <button onClick={onReload} disabled={loading}>
            {loading ? "Loading..." : "Reload Dashboard"}
          </button>
          <button className="secondary" onClick={onRefreshTicker}>
            Refresh {activeTicker}
          </button>
          <button className="ghost" onClick={onRefreshWatchlist}>
            Refresh Watchlist
          </button>
        </div>

        {notice ? <div className="notice">{notice}</div> : null}
      </div>

      <form className="command-card" onSubmit={onAddTicker}>
        <label htmlFor="active-ticker">Active ticker</label>
        <input
          id="active-ticker"
          value={activeTicker}
          onChange={(event) => onActiveTickerChange(event.target.value)}
          onBlur={onTickerBlur}
        />

        <label htmlFor="period-select">Period</label>
        <select
          id="period-select"
          value={period}
          onChange={(event) => onPeriodChange(event.target.value)}
        >
          {PERIOD_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>

        <label htmlFor="add-ticker">Add validated ticker</label>
        <div className="inline-form">
          <input
            id="add-ticker"
            value={pendingTicker}
            onChange={(event) => onPendingTickerChange(event.target.value)}
            placeholder="Example: IBM"
          />
          <button disabled={validating}>{validating ? "Checking" : "Add"}</button>
        </div>

        <p className="microcopy">
          Validation uses existing cache first, then the provider refresh path. Valid symbols are
          stored as ticker subtabs.
        </p>
      </form>
    </header>
  );
}
