import { Badge } from "../../components/common/Badge.jsx";
import { ensureArray } from "../../utils/arrays.js";
import { truncateText } from "../../utils/formatters.js";

export function CensusIndicatorCard({ item, selected, onToggle }) {
  return (
    <article className="discovery-card">
      <div className="panel-heading discovery-card-head">
        <div>
          <p className="eyebrow">Indicator candidate</p>
          <h3>{truncateText(item.label || item.variable_name, 120)}</h3>
        </div>
        <Badge value={item.market_relevance || "neutral"} />
      </div>

      <p className="muted small">
        {item.variable_name} | {item.dataset_title}
      </p>
      <p>{truncateText(item.concept || item.dataset_title, 200)}</p>

      <div className="storage-record-stats">
        <span>{item.dataset_family_id}</span>
        {item.group ? <span>Group {item.group}</span> : null}
        {ensureArray(item.matched_terms)
          .slice(0, 4)
          .map((term) => (
            <span key={term}>{term}</span>
          ))}
      </div>

      <div className="comparison-actions">
        <button type="button" className={selected ? "ghost" : "secondary"} onClick={() => onToggle(item)}>
          {selected ? "Remove" : "Compare"}
        </button>
        {item.variables_url ? (
          <a href={item.variables_url} target="_blank" rel="noreferrer">
            Metadata
          </a>
        ) : null}
      </div>
    </article>
  );
}
