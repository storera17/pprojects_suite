import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";

export function AutoAgentPanel({ agent, runs, onRefreshStale, onRunNow }) {
  const states = Array.isArray(agent.ticker_states) ? agent.ticker_states : [];
  const recentRuns = Array.isArray(runs) ? runs : [];
  const lastRun = agent.last_run || {};
  const staleCount = Number(agent.stale_categories || 0);

  return (
    <section className="panel wide auto-agent-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Autonomous cache management</p>
          <h2>Auto Cached Agent</h2>
        </div>
        <Badge value={agent.enabled ? (staleCount ? "refresh needed" : "monitoring") : "disabled"} />
      </div>

      <p className="muted">
        The agent checks SQLite freshness, skips fresh provider categories, refreshes stale or
        missing data, and serves stale cache if providers rate-limit.
      </p>

      <div className="agent-metrics">
        <span>
          <b>{agent.enabled ? "enabled" : "disabled"}</b>
          <small>status</small>
        </span>
        <span>
          <b>{agent.interval_minutes || "n/a"} min</b>
          <small>check interval</small>
        </span>
        <span>
          <b>{Math.round((agent.ttl_seconds || 0) / 3600)} hr</b>
          <small>cache TTL</small>
        </span>
        <span>
          <b>{staleCount}</b>
          <small>stale missing categories</small>
        </span>
        <span>
          <b>{agent.fallback_count || 0}</b>
          <small>fallbacks active</small>
        </span>
        <span>
          <b>{lastRun.started_at || "never"}</b>
          <small>last run</small>
        </span>
      </div>

      <div className="hero-actions small-actions">
        <button onClick={onRefreshStale}>Refresh Stale Only</button>
        <button className="secondary" onClick={onRunNow}>
          Force Agent Run
        </button>
      </div>

      <div className="agent-grid">
        {states.map((state) => (
          <article className="agent-card" key={state.ticker}>
            <div className="provider-top">
              <strong>{state.ticker}</strong>
              <Badge value={state.state} />
            </div>
            <div className="provider-facts">
              <span>
                <b>{state.fresh_categories}</b>
                <small>fresh</small>
              </span>
              <span>
                <b>{state.stale_categories}</b>
                <small>stale</small>
              </span>
              <span>
                <b>{state.missing_categories}</b>
                <small>missing</small>
              </span>
              <span>
                <b>{state.critical_ready ? "yes" : "no"}</b>
                <small>price quote ready</small>
              </span>
            </div>
          </article>
        ))}
      </div>

      <div className="run-log">
        <h3>Recent Agent Runs</h3>
        {!recentRuns.length ? <EmptyState title="No auto cached agent run has been logged yet." /> : null}
        {recentRuns.slice(0, 5).map((run) => (
          <div className="mini-row" key={run.id}>
            <span>{run.started_at}</span>
            <Badge value={run.status} />
            <small>{run.message || run.mode}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
