export function EmptyState({ title = "No stored data yet", children }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{children || "Refresh this ticker or watchlist to populate the local SQLite cache."}</p>
    </div>
  );
}
