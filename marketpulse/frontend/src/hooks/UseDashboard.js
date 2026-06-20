import { useEffect, useState } from "react";

import {
  getDashboard,
  getHealth,
  getKeyStatus,
  getProviderStatus,
  refreshAll,
  refreshTicker,
} from "../api/dashboardApi.js";
import { getDailyReport, generateBrief, getLatestBrief } from "../api/reportApi.js";
import { getWatchlist, validateTicker } from "../api/tickerApi.js";
import { DEFAULT_TICKERS } from "../constants/tickers.js";
import { ensureArray, ensureObject } from "../utils/arrays.js";
import { normalizeTicker } from "../utils/symbols.js";

export function useDashboard() {
  const [activeTicker, setActiveTicker] = useState(DEFAULT_TICKERS[0]);
  const [period, setPeriod] = useState("daily");
  const [activeSection, setActiveSection] = useState("overview");
  const [watchlist, setWatchlist] = useState(DEFAULT_TICKERS);
  const [pendingTicker, setPendingTicker] = useState("");

  const [health, setHealth] = useState({ status: "checking" });
  const [keyStatus, setKeyStatus] = useState({ required_for_full_data: {} });
  const [dashboard, setDashboard] = useState({});
  const [providerStatuses, setProviderStatuses] = useState([]);
  const [latestBrief, setLatestBrief] = useState(null);
  const [reportText, setReportText] = useState("");

  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [briefLoading, setBriefLoading] = useState(false);
  const [notice, setNotice] = useState("");

  async function loadDashboard(nextTicker = activeTicker, nextPeriod = period) {
    setLoading(true);
    setNotice("");
    const symbol = normalizeTicker(nextTicker || DEFAULT_TICKERS[0]);

    try {
      const [healthResponse, keyResponse, watchlistResponse, dashboardResponse, providerResponse, briefResponse] =
        await Promise.all([
          getHealth(),
          getKeyStatus(),
          getWatchlist(),
          getDashboard(symbol, nextPeriod),
          getProviderStatus(),
          getLatestBrief("watchlist"),
        ]);

      setHealth(ensureObject(healthResponse));
      setKeyStatus(ensureObject(keyResponse));
      setLatestBrief(ensureObject(briefResponse).report || null);

      const nextWatchlist = ensureArray(watchlistResponse?.tickers)
        .map(normalizeTicker)
        .filter(Boolean);
      setWatchlist((current) => {
        const source = nextWatchlist.length ? nextWatchlist : DEFAULT_TICKERS;
        return Array.from(new Set([...source, ...current]));
      });

      const nextDashboard = ensureObject(dashboardResponse);
      setDashboard(nextDashboard);
      setProviderStatuses(
        ensureArray(nextDashboard.provider_statuses).length
          ? ensureArray(nextDashboard.provider_statuses)
          : ensureArray(providerResponse?.providers),
      );

      if (healthResponse?.offline || healthResponse?.status === "error") {
        setNotice("Backend API is not reachable at http://localhost:8000/api. Start FastAPI and reload the page.");
      }
    } catch (error) {
      setNotice(error?.message || "Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard(DEFAULT_TICKERS[0], "daily");
  }, []);

  async function reloadDashboard() {
    await loadDashboard(activeTicker, period);
  }

  async function selectTicker(ticker) {
    const symbol = normalizeTicker(ticker);
    setActiveTicker(symbol);
    setActiveSection("overview");
    setReportText("");
    await loadDashboard(symbol, period);
  }

  async function changePeriod(nextPeriod) {
    setPeriod(nextPeriod);
    await loadDashboard(activeTicker, nextPeriod);
  }

  async function refreshActiveTicker() {
    setNotice("");
    const response = await refreshTicker(activeTicker);
    if (response?.status === "error") {
      setNotice(response.error || "Ticker refresh failed.");
    }
    await loadDashboard(activeTicker, period);
  }

  async function refreshWatchlist() {
    setNotice("");
    const response = await refreshAll(watchlist);
    if (response?.status === "error") {
      setNotice(response.error || "Watchlist refresh failed.");
    }
    await loadDashboard(activeTicker, period);
  }

  async function validatePendingTicker(event) {
    event.preventDefault();
    const symbol = normalizeTicker(pendingTicker);
    if (!symbol) {
      return;
    }
    setValidating(true);
    setNotice("");

    try {
      const response = await validateTicker(symbol);
      if (!response?.valid) {
        setNotice(response?.message || `${symbol} could not be validated by the local provider layer.`);
        return;
      }

      const validatedWatchlist = ensureArray(response?.watchlist)
        .map(normalizeTicker)
        .filter(Boolean);
      setWatchlist((current) =>
        Array.from(new Set([...(validatedWatchlist.length ? validatedWatchlist : [symbol]), ...current])),
      );
      setPendingTicker("");
      await selectTicker(symbol);
    } finally {
      setValidating(false);
    }
  }

  async function generateReport() {
    setReportText("Generating local SQLite report...");
    const response = await getDailyReport(activeTicker, period);
    setReportText(response?.report || response?.error || "No report returned.");
  }

  async function generateDailyBrief() {
    setBriefLoading(true);
    setNotice("");
    try {
      const response = await generateBrief(watchlist);
      if (response?.status === "error") {
        setNotice(response.error || "Daily brief generation failed.");
        return;
      }
      const latest = await getLatestBrief("watchlist");
      setLatestBrief(ensureObject(latest).report || null);
    } finally {
      setBriefLoading(false);
    }
  }

  return {
    activeTicker,
    setActiveTicker: (value) => setActiveTicker(normalizeTicker(value)),
    period,
    activeSection,
    setActiveSection,
    watchlist,
    pendingTicker,
    setPendingTicker: (value) => setPendingTicker(normalizeTicker(value)),
    health,
    keyStatus,
    dashboard,
    providerStatuses,
    latestBrief,
    reportText,
    loading,
    validating,
    briefLoading,
    notice,
    setNotice,
    loadDashboard,
    reloadDashboard,
    selectTicker,
    changePeriod,
    refreshActiveTicker,
    refreshWatchlist,
    validatePendingTicker,
    generateReport,
    generateDailyBrief,
  };
}
