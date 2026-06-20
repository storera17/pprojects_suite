export function TickerTabs({ tickers, selected, onSelect }) {
  return (
    <nav className="ticker-tabs" aria-label="Ticker tabs">
      {tickers.map((ticker) => (
        <button
          key={ticker}
          className={ticker === selected ? "ticker-tab active" : "ticker-tab"}
          onClick={() => onSelect(ticker)}
        >
          {ticker}
        </button>
      ))}
    </nav>
  );
}
