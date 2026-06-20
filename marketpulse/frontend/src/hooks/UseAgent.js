import { useEffect, useState } from "react";

import { getTickerAvailability, getTickerRecords } from "../api/tickerApi.js";
import { ensureArray, ensureObject } from "../utils/arrays.js";
import { normalizeTicker } from "../utils/symbols.js";

const DEFAULT_FILTERS = { category: "", provider: "", days: 365, limit: 10 };

export function useTickerStorage(activeTicker) {
  const [storageSymbol, setStorageSymbol] = useState(normalizeTicker(activeTicker || "SPY"));
  const [availability, setAvailability] = useState({
    status: "idle",
    ticker: "SPY",
    has_data: false,
    record_count: 0,
    categories: {},
    providers: {},
    message: "",
  });
  const [recordsPayload, setRecordsPayload] = useState({ status: "idle", ticker: "SPY", count: 0, records: [] });
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function inspectStorage(nextSymbol = storageSymbol || activeTicker, nextFilters = filters) {
    const symbol = normalizeTicker(nextSymbol || activeTicker || "SPY");
    setLoading(true);
    setError("");
    setStorageSymbol(symbol);

    try {
      const [availabilityResponse, recordsResponse] = await Promise.all([
        getTickerAvailability(symbol),
        getTickerRecords(symbol, nextFilters),
      ]);

      setAvailability(ensureObject(availabilityResponse));
      setRecordsPayload({
        ...ensureObject(recordsResponse),
        records: ensureArray(recordsResponse?.records),
      });

      if (availabilityResponse?.status === "error") {
        setError(availabilityResponse.error || availabilityResponse.message || `Could not inspect ${symbol}.`);
      } else if (recordsResponse?.status === "error") {
        setError(recordsResponse.error || `Could not load stored rows for ${symbol}.`);
      }
    } catch (caughtError) {
      setError(caughtError?.message || `Could not inspect ${symbol}.`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const symbol = normalizeTicker(activeTicker || "SPY");
    setStorageSymbol(symbol);
    inspectStorage(symbol, filters);
  }, [activeTicker]);

  async function updateFilter(field, value) {
    const nextFilters = { ...filters, [field]: value };
    setFilters(nextFilters);
    await inspectStorage(storageSymbol || activeTicker, nextFilters);
  }

  async function useActiveTicker() {
    const symbol = normalizeTicker(activeTicker || "SPY");
    setStorageSymbol(symbol);
    await inspectStorage(symbol, filters);
  }

  return {
    storageSymbol,
    setStorageSymbol: (value) => setStorageSymbol(normalizeTicker(value)),
    availability,
    recordsPayload,
    filters,
    loading,
    error,
    inspectStorage,
    updateFilter,
    useActiveTicker,
  };
}
