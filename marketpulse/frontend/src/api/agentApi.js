import { request } from "./client.js";

export function getAutoAgentStatus() {
  return request("/agent/status", {}, { status: "error", enabled: false, ticker_states: [] });
}

export function getAutoAgentRuns(limit = 10) {
  return request(`/agent/runs?limit=${encodeURIComponent(limit)}`, {}, { status: "error", runs: [] });
}

export function runAutoAgent(tickers = [], force = false) {
  return request(
    "/agent/run",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tickers, force }),
    },
    { status: "error" },
  );
}

export function refreshStaleWithAgent(tickers = []) {
  return request(
    "/agent/refresh-stale",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tickers, force: false }),
    },
    { status: "error" },
  );
}

export function sendAgentMessage(message, ticker = "SPY", period = "daily") {
  return request(
    "/agent/chat",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, ticker, period, user_id: "local_user" }),
    },
    { status: "error", answer: "No response returned." },
  );
}
