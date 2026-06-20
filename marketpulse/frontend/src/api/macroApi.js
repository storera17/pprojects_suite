import { request } from "./client.js";

export function searchCensusDiscovery(query = "", options = {}) {
  const params = new URLSearchParams();
  if (query) {
    params.set("q", query);
  }
  if (options.kind) {
    params.set("kind", options.kind);
  }
  if (options.datasetLimit) {
    params.set("dataset_limit", String(options.datasetLimit));
  }
  if (options.indicatorLimit) {
    params.set("indicator_limit", String(options.indicatorLimit));
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request(`/macro/census/discovery${suffix}`, {}, {
    status: "error",
    source: "census_public_metadata",
    metadata_access: { api_key_required: false, data_queries_require_api_key: true },
    dataset_matches: [],
    indicator_matches: [],
    featured_queries: [],
    datasets_scanned: 0,
  });
}

export function getCryptoTokens() {
  return request("/crypto/tokens", {}, { status: "error", cached_records: [] });
}

export function getForexRates() {
  return request("/forex/rates", {}, { status: "error", cached_records: [] });
}
