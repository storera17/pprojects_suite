import { Badge } from "../../components/common/Badge.jsx";
import { ensureArray } from "../../utils/arrays.js";
import { titleCase, truncateText } from "../../utils/formatters.js";

export function CensusDatasetCard({ item }) {
  return (
    <article className="discovery-card">
      <div className="panel-heading discovery-card-head">
        <div>
          <p className="eyebrow">Dataset family</p>
          <h3>{item.title}</h3>
        </div>
        <Badge value={item.market_relevance || "neutral"} />
      </div>

      <p className="muted small">
        {titleCase(item.dataset_type)}
        {item.vintage ? ` | ${item.vintage}` : " | latest metadata"}
      </p>
      <p>{truncateText(item.description, 260)}</p>

      <div className="storage-record-stats">
        <span>{item.family_id}</span>
        {ensureArray(item.matched_terms)
          .slice(0, 4)
          .map((term) => (
            <span key={term}>{term}</span>
          ))}
      </div>

      <footer className="discovery-links">
        {item.variables_url ? (
          <a href={item.variables_url} target="_blank" rel="noreferrer">
            Variables
          </a>
        ) : null}
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
      </footer>
    </article>
  );
}
