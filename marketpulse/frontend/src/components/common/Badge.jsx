export function Badge({ value }) {
  const normalized = String(value || "unknown").toLowerCase().replace(/\s+/g, "_");
  return <span className={`badge ${normalized}`}>{normalized.replace(/_/g, " ")}</span>;
}
