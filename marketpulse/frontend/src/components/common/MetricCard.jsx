export function MetricCard({ label, value, detail, accent }) {
  return (
    <article className={`metric-card ${accent || ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}
