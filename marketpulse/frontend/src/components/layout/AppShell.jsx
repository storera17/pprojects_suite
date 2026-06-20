export function AppShell({ header, freshness, agentPanel, quality, tickerTabs, sectionTabs, children }) {
  return (
    <div className="app">
      {header}
      {freshness}
      {agentPanel}
      {quality}
      {tickerTabs}
      {sectionTabs}
      {children}
    </div>
  );
}
