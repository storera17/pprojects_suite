import { request } from "./client.js";

export function getDailyReport(ticker = "SPY", period = "daily") {
  return request(
    `/reports/daily/${encodeURIComponent(ticker)}?period=${encodeURIComponent(period)}`,
    {},
    { status: "error", report: "" },
  );
}

export function getLatestBrief(scope = "watchlist", ticker = null) {
  const params = new URLSearchParams({ scope });
  if (ticker) {
    params.set("ticker", ticker);
  }
  return request(`/reports/brief/latest?${params.toString()}`, {}, { status: "error", report: null });
}

export function generateBrief(tickers = []) {
  return request(
    "/reports/brief/generate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tickers }),
    },
    { status: "error", report: "" },
  );
}
