import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";
import { ensureArray, ensureObject } from "../../utils/arrays.js";
import { CensusComparisonPanel } from "./CensusComparisonPanel.jsx";
import { CensusDatasetCard } from "./CensusDatasetCard.jsx";
import { CensusIndicatorCard } from "./CensusIndicatorCard.jsx";

export function CensusDiscoveryPanel({
  query,
  onQueryChange,
  kind,
  onKindChange,
  results,
  loading,
  error,
  onSearch,
  onChooseQuery,
  compareItems,
  onToggleCompare,
  onClearCompare,
}) {
  const datasetMatches = ensureArray(results.dataset_matches);
  const indicatorMatches = ensureArray(results.indicator_matches);
  const featuredQueries = ensureArray(results.featured_queries);
  const metadataAccess = ensureObject(results.metadata_access);
  const metadataReady = !metadataAccess.api_key_required;

  return (
    <section className="dashboard-grid one">
      <section className="panel wide census-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Public Census discovery</p>
            <h2>Census Macro Discovery</h2>
          </div>
          <Badge value={metadataReady ? "configured" : "missing"} />
        </div>

        <p className="muted">
          Search public Census metadata for datasets and indicator candidates before deciding what
          should be ingested into SQLite. This explorer reads metadata only and does not write any
          rows.
        </p>

        <form className="census-search-form" onSubmit={onSearch}>
          <div className="census-search-box">
            <label htmlFor="census-query">Search Census metadata</label>
            <input
              id="census-query"
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="Examples: employment, retail sales, housing vacancy, commuting"
            />
          </div>

          <div>
            <label htmlFor="census-kind">Scope</label>
            <select id="census-kind" value={kind} onChange={(event) => onKindChange(event.target.value)}>
              <option value="all">Datasets + Indicators</option>
              <option value="datasets">Datasets Only</option>
              <option value="indicators">Indicators Only</option>
            </select>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search Census"}
          </button>
        </form>

        <div className="featured-query-row">
          {(featuredQueries.length ? featuredQueries : ["employment", "income", "housing", "trade"]).map(
            (value) => (
              <button
                type="button"
                className="ghost featured-pill"
                key={value}
                onClick={() => onChooseQuery(value)}
              >
                {value}
              </button>
            ),
          )}
        </div>

        <div className="storage-record-stats">
          <span>{metadataReady ? "No Census API key needed for metadata search" : "Metadata access changed"}</span>
          <span>{metadataAccess.data_queries_require_api_key ? "Raw data pulls still require a Census API key" : "Raw data pulls are public"}</span>
          <span>{results.datasets_scanned || 0} dataset families scanned</span>
        </div>

        {error ? <div className="notice">{error}</div> : null}

        <div className="analytics-grid two discovery-sections">
          <div className="chart-card discovery-section">
            <div className="panel-heading">
              <h3>Dataset Matches</h3>
              <span>{datasetMatches.length}</span>
            </div>
            {!datasetMatches.length ? (
              <EmptyState title="No dataset matches">
                Try a broader query like income, employment, trade, or housing.
              </EmptyState>
            ) : null}
            <div className="discovery-grid">
              {datasetMatches.map((item) => (
                <CensusDatasetCard item={item} key={item.dataset_id} />
              ))}
            </div>
          </div>

          <div className="chart-card discovery-section">
            <div className="panel-heading">
              <h3>Indicator Matches</h3>
              <span>{indicatorMatches.length}</span>
            </div>
            {!query && !indicatorMatches.length ? (
              <EmptyState title="Search to find indicators">
                Enter a macro theme above to fetch variable-level indicator candidates and compare
                them.
              </EmptyState>
            ) : null}
            {query && !indicatorMatches.length ? (
              <EmptyState title="No indicator matches">
                This search surfaced datasets but no strong indicator candidates yet. Try a narrower
                term like median income or payroll.
              </EmptyState>
            ) : null}
            <div className="discovery-grid">
              {indicatorMatches.map((item) => (
                <CensusIndicatorCard
                  item={item}
                  key={item.indicator_id}
                  selected={compareItems.some((entry) => entry.indicator_id === item.indicator_id)}
                  onToggle={onToggleCompare}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      <CensusComparisonPanel items={compareItems} onToggle={onToggleCompare} onClear={onClearCompare} />
    </section>
  );
}
