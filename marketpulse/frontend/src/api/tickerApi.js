import { request } from "./client.js";
import { DEFAULT_TICKERS } from "../constants/tickers.js";

export function getWatchlist() {
  return request("/tickers/watchlist", {}, { status: "error", tickers: DEFAULT_TICKERS });
}

export function validateTicker(ticker) {
  return request(
    "/tickers/validate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    },
    { status: "error", valid: false, ticker },
  );
}

export function getTickerAvailability(ticker = "SPY") {
  return request(
    `/tickers/${encodeURIComponent(ticker)}/availability`,
    {},
    { status: "error", ticker, has_data: false, record_count: 0, categories: {}, providers: {} },
  );
}

export function getTickerRecords(ticker = "SPY", options = {}) {
  const params = new URLSearchParams();
  if (options.category) {
    params.set("category", options.category);
  }
  if (options.provider) {
    params.set("provider", options.provider);
  }
  if (options.days) {
    params.set("days", String(options.days));
  }
  if (options.limit) {
    params.set("limit", String(options.limit));
  }
  const suffix = params.toString();
  return request(
    `/tickers/${encodeURIComponent(ticker)}/records${suffix ? `?${suffix}` : ""}`,
    {},
    { status: "error", ticker, count: 0, records: [] },
  );
}
