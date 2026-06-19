import { request } from "./client";

export function getDashboard(ticker = "SPY", period = "daily") {
  return request(
    `/dashboard/${encodeURIComponent(ticker)}?period=${encodeURIComponent(period)}`,
    {},
    { status: "error", ticker, period }
  );
}

export function getHealth() {
  return request("/health", {}, { status: "offline" });
}

export function getProviderStatus() {
  return request("/providers/status", {}, { status: "error", providers: [] });
}