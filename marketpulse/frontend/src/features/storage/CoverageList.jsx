import { Badge } from "../../components/common/Badge.jsx";
import { ensureObject } from "../../utils/arrays.js";
import { formatNumber, titleCase } from "../../utils/formatters.js";

export function CoverageList({ title, rows, tone = "neutral" }) {
  const entries = Object.entries(ensureObject(rows)).sort((left, right) => right[1] - left[1]);

  return (
    <div className="storage-coverage-card">
      <div className="storage-coverage-head">
        <h3>{title}</h3>
        <Badge value={tone} />
      </div>
      {!entries.length ? <p className="muted small">No stored coverage yet.</p> : null}
      <div className="storage-chip-grid">
        {entries.map(([label, count]) => (
          <div className="storage-chip" key={label}>
            <span>{titleCase(label)}</span>
            <b>
              {formatNumber(count, 0)} row{Number(count) === 1 ? "" : "s"}
            </b>
          </div>
        ))}
      </div>
    </div>
  );
}
