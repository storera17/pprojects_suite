import { Badge } from "../../components/common/Badge.jsx";
import { EmptyState } from "../../components/common/EmptyState.jsx";
import { ensureArray } from "../../utils/arrays.js";
import { titleCase, truncateText } from "../../utils/formatters.js";

export function CensusComparisonPanel({ items, onToggle, onClear }) {
  const selected = ensureArray(items);

  return (
    <section className="panel wide comparison-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Shortlist before SQLite</p>
          <h2>Indicator Comparison</h2>
        </div>
        {selected.length ? (
          <button type="button" className="ghost" onClick={onClear}>
            Clear Compare
          </button>
        ) : null}
      </div>

      {!selected.length ? (
        <EmptyState title="No indicators selected">
          Search Census metadata, then add up to four candidates for side-by-side comparison.
        </EmptyState>
      ) : (
        <div className="comparison-grid">
          {selected.map((item) => (
            <article className="comparison-card" key={item.indicator_id}>
              <div className="comparison-card-top">
                <div>
                  <strong>{truncateText(item.label || item.variable_name, 120)}</strong>
                  <p>{item.variable_name}</p>
                </div>
                <Badge value={item.market_relevance || "neutral"} />
              </div>

              <div className="comparison-facts">
                <span>
                  <b>{item.dataset_title}</b>
                  <small>dataset</small>
                </span>
                <span>
                  <b>{item.dataset_vintage || "latest"}</b>
                  <small>vintage</small>
                </span>
                <span>
                  <b>{titleCase(item.dataset_type)}</b>
                  <small>type</small>
                </span>
                <span>
                  <b>{item.group || "N/A"}</b>
                  <small>group</small>
                </span>
              </div>

              <p>{truncateText(item.concept || item.dataset_title, 220)}</p>

              <div className="storage-record-stats">
                <span>{item.dataset_family_id}</span>
                {ensureArray(item.matched_terms)
                  .slice(0, 4)
                  .map((term) => (
                    <span key={term}>{term}</span>
                  ))}
              </div>

              <div className="comparison-actions">
                <button type="button" className="ghost" onClick={() => onToggle(item)}>
                  Remove
                </button>
                {item.geography_url ? (
                  <a href={item.geography_url} target="_blank" rel="noreferrer">
                    Geography
                  </a>
                ) : null}
                {item.documentation_url ? (
                  <a href={item.documentation_url} target="_blank" rel="noreferrer">
                    Docs
                  </a>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
