import { useEffect, useState } from "react";

import { searchCensusDiscovery } from "../api/macroApi.js";
import { ensureArray, ensureObject } from "../utils/arrays.js";

export function useCensusDiscovery() {
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("all");
  const [results, setResults] = useState({
    status: "idle",
    metadata_access: { api_key_required: false, data_queries_require_api_key: true },
    featured_queries: [],
    dataset_matches: [],
    indicator_matches: [],
    datasets_scanned: 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [compareItems, setCompareItems] = useState([]);

  async function search(nextQuery = query, nextKind = kind) {
    setLoading(true);
    setError("");
    try {
      const response = await searchCensusDiscovery(nextQuery, {
        kind: nextKind,
        datasetLimit: 8,
        indicatorLimit: 14,
      });
      setResults({
        ...ensureObject(response),
        featured_queries: ensureArray(response?.featured_queries),
        dataset_matches: ensureArray(response?.dataset_matches),
        indicator_matches: ensureArray(response?.indicator_matches),
        metadata_access: ensureObject(response?.metadata_access),
      });
      if (response?.status === "error") {
        setError(response.error || "Census metadata search failed.");
      }
    } catch (caughtError) {
      setError(caughtError?.message || "Census metadata search failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    search("", "all");
  }, []);

  async function chooseFeaturedQuery(value) {
    setQuery(value);
    await search(value, kind);
  }

  async function changeKind(value) {
    setKind(value);
    await search(query, value);
  }

  function toggleCompare(item) {
    setCompareItems((current) =>
      current.some((entry) => entry.indicator_id === item.indicator_id)
        ? current.filter((entry) => entry.indicator_id !== item.indicator_id)
        : [item, ...current].slice(0, 4),
    );
  }

  return {
    query,
    setQuery,
    kind,
    setKind,
    results,
    loading,
    error,
    compareItems,
    search,
    chooseFeaturedQuery,
    changeKind,
    toggleCompare,
    clearCompare: () => setCompareItems([]),
  };
}
