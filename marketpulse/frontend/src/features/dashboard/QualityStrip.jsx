import { ensureArray } from "../../utils/arrays.js";
import { titleCase } from "../../utils/formatters.js";

export function QualityStrip({ quality }) {
  const missing = ensureArray(quality.missing);

  return (
    <section className="quality-strip">
      <div>
        <span>Workspace readiness</span>
        <b>{titleCase(quality.status || "unknown")}</b>
      </div>
      <div>
        <span>Coverage score</span>
        <b>{quality.coverage_score ?? 0}/100</b>
      </div>
      <div>
        <span>Price</span>
        <b>{quality.price_available ? "available" : "missing"}</b>
      </div>
      <div>
        <span>Volume</span>
        <b>{quality.volume_available ? "available" : "unavailable"}</b>
      </div>
      <div>
        <span>News Sentiment</span>
        <b>{quality.news_available ? "ready" : "partial"}</b>
      </div>
      <div className="wide-quality">
        <span>Missing</span>
        <b>{missing.length ? missing.join(", ") : "none"}</b>
      </div>
    </section>
  );
}
