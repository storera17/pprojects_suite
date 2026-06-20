import { formatAge } from "../../utils/formatters.js";

export function DataFreshness({ summary, health }) {
  return (
    <section className="freshness-strip">
      <div>
        <span>Backend</span>
        <b>{health.status || "checking"}</b>
      </div>
      <div>
        <span>Last refresh</span>
        <b>{summary.last_refreshed_at || "not recorded"}</b>
      </div>
      <div>
        <span>Freshest cache</span>
        <b>{formatAge(summary.freshest_cache_age_minutes)}</b>
      </div>
      <div>
        <span>API calls skipped</span>
        <b>{summary.api_skipped_count ?? 0}</b>
      </div>
      <div>
        <span>Fallbacks</span>
        <b>{summary.degraded_fallback_count ?? summary.rate_limit_fallback_count ?? 0}</b>
      </div>
    </section>
  );
}
