import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";
import { ensureArray, ensureObject } from "../../utils/arrays.js";
import { formatAge } from "../../utils/formatters.js";

function providerBadgeValue(provider) {
  if (provider?.fallback_active) {
    return "degraded";
  }
  const status = String(provider?.status || "unknown").toLowerCase();
  return status === "method_not_allowed" ? "unavailable" : status;
}

function providerFooter(provider) {
  if (provider?.fallback_active) {
    return `${provider.fallback_reason || provider.provider_error_status || "provider unavailable"}: serving stored SQLite cache while live requests are unavailable.`;
  }
  if (provider?.rate_limit_fallback) {
    return "Rate-limit fallback is serving stored SQLite data.";
  }
  return `Collected ${provider.cache_collected_at || provider.last_success_at || "n/a"}`;
}

export function ProviderPanel({ providers, keyStatus }) {
  const items = ensureArray(providers);
  const keys = ensureObject(keyStatus.required_for_full_data);
  const degradedCount = items.filter((provider) => provider.fallback_active || provider.rate_limit_fallback).length;
  const configuredCount = Object.values(keys).filter(Boolean).length;

  return (
    <section className="dashboard-grid">
      <section className="panel" id="providers">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Cache-first ingestion</p>
            <h2>Provider Health</h2>
          </div>
          <Badge value={degradedCount ? "degraded but covered" : "protected"} />
        </div>

        {!items.length ? (
          <EmptyState title="No provider status yet">
            Run a refresh to populate provider health and cache metadata.
          </EmptyState>
        ) : (
          <div className="provider-grid">
            {items.map((provider) => (
              <article className="provider-card" key={provider.provider || provider.name}>
                <div className="provider-top">
                  <strong>{provider.provider || provider.name}</strong>
                  <Badge value={providerBadgeValue(provider)} />
                </div>
                <p>{provider.message || "No provider message returned."}</p>
                <div className="provider-facts">
                  <span>
                    <b>{provider.cache_source || provider.source || "unknown"}</b>
                    <small>source</small>
                  </span>
                  <span>
                    <b>{formatAge(provider.cache_age_minutes)}</b>
                    <small>cache age</small>
                  </span>
                  <span>
                    <b>{provider.cache_record_count ?? "n/a"}</b>
                    <small>rows</small>
                  </span>
                  <span>
                    <b>{provider.cache_fresh ? "fresh" : "stale"}</b>
                    <small>state</small>
                  </span>
                </div>
                <footer className={provider.fallback_active || provider.rate_limit_fallback ? "warning-text" : "muted"}>
                  {providerFooter(provider)}
                </footer>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>API Key Coverage</h2>
          <span>
            {configuredCount}/{Object.keys(keys).length || 0}
          </span>
        </div>
        {Object.entries(keys).map(([name, configured]) => (
          <div className="key-row" key={name}>
            <span>{name.replace("_API_KEY", "")}</span>
            <Badge value={configured ? "configured" : "missing"} />
          </div>
        ))}
      </section>
    </section>
  );
}
