from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests


CATALOG_URL = "https://api.census.gov/data.json"
REQUEST_TIMEOUT_SECONDS = 35
CATALOG_TTL_SECONDS = 3600
VARIABLES_TTL_SECONDS = 21600
MAX_INDICATOR_DATASETS = 6
FEATURED_QUERIES = [
    "employment",
    "income",
    "poverty",
    "housing",
    "retail sales",
    "trade",
]
DEFAULT_DISCOVERY_QUERY = "employment income poverty housing retail sales trade business payroll population"
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}
ECONOMIC_KEYWORDS = {
    "business": 3,
    "commuting": 2,
    "construction": 3,
    "earnings": 4,
    "economy": 4,
    "employment": 5,
    "exports": 4,
    "housing": 5,
    "imports": 4,
    "income": 5,
    "industry": 3,
    "jobs": 4,
    "labor": 4,
    "payroll": 4,
    "population": 2,
    "poverty": 5,
    "prices": 3,
    "retail": 5,
    "sales": 4,
    "trade": 5,
    "unemployment": 5,
    "vacancy": 4,
    "wages": 4,
}
PREFERRED_FAMILY_PREFIXES = (
    "acs/",
    "cbp",
    "ecnbasic",
    "eits",
    "intltrade/",
    "pep/",
    "timeseries/",
    "zbp",
)
EXCLUDED_VARIABLE_SUFFIXES = ("EA", "MA", "M", "MOE", "PMA", "PM", "LB90", "UB90")


_session = requests.Session()
_catalog_cache: dict[str, Any] = {"expires_at": 0.0, "value": []}
_variables_cache: dict[str, dict[str, Any]] = {}


def _now() -> float:
    return time.time()


def _normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    return str(url).replace("http://api.census.gov", "https://api.census.gov")


def _tokenize(text: str | None) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", str(text or "").lower())
    return [token for token in tokens if token not in STOPWORDS]


def _clean_label(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("!!", " > ")).strip()


def _catalog_json() -> dict[str, Any]:
    cached = _catalog_cache
    if cached["expires_at"] > _now() and cached["value"]:
        return cached["value"]

    response = _session.get(CATALOG_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    _catalog_cache["expires_at"] = _now() + CATALOG_TTL_SECONDS
    _catalog_cache["value"] = payload
    return payload


def _strip_vintage_prefix(dataset_id: str) -> str:
    parts = [part for part in str(dataset_id or "").split("/") if part]
    if parts and re.fullmatch(r"\d{4}", parts[0]):
        return "/".join(parts[1:])
    return "/".join(parts)


def _dataset_type(item: dict[str, Any], dataset_id: str) -> str:
    if item.get("c_isMicrodata"):
        return "microdata"
    if dataset_id.startswith("timeseries/"):
        return "time_series"
    return "aggregate"


def _economic_bonus(text: str) -> int:
    lower = str(text or "").lower()
    score = 0
    for keyword, weight in ECONOMIC_KEYWORDS.items():
        if keyword in lower:
            score += weight
    return score


def _family_bonus(family_id: str) -> int:
    if not family_id:
        return 0
    if family_id.startswith(PREFERRED_FAMILY_PREFIXES):
        return 5
    return 0


def _normalize_dataset(item: dict[str, Any]) -> dict[str, Any] | None:
    distribution = item.get("distribution") or []
    access_url = None
    for entry in distribution:
        access_url = entry.get("accessURL")
        if access_url:
            break

    api_base_url = _normalize_url(access_url)
    if not api_base_url:
        path_bits = item.get("c_dataset") or []
        vintage = item.get("c_vintage")
        if vintage:
            api_base_url = f"https://api.census.gov/data/{vintage}/{'/'.join(path_bits)}"
        elif path_bits:
            api_base_url = f"https://api.census.gov/data/{'/'.join(path_bits)}"

    if not api_base_url or "/data/" not in api_base_url:
        return None

    dataset_id = api_base_url.split("/data/", 1)[1].strip("/")
    family_id = _strip_vintage_prefix(dataset_id)
    title = str(item.get("title") or family_id)
    description = str(item.get("description") or "")
    title_text = " ".join([title, dataset_id, family_id.replace("/", " ")]).lower()
    description_text = description.lower()
    return {
        "dataset_id": dataset_id,
        "family_id": family_id,
        "title": title,
        "description": description,
        "vintage": item.get("c_vintage"),
        "dataset_type": _dataset_type(item, dataset_id),
        "api_base_url": api_base_url,
        "variables_url": _normalize_url(item.get("c_variablesLink")),
        "geography_url": _normalize_url(item.get("c_geographyLink")),
        "documentation_url": _normalize_url(item.get("c_documentationLink")),
        "examples_url": _normalize_url(item.get("c_examplesLink")),
        "title_text": title_text,
        "description_text": description_text,
        "economic_bonus": _economic_bonus(f"{title_text} {description_text}"),
        "family_bonus": _family_bonus(family_id),
    }


def _prefer_dataset(candidate: dict[str, Any], current: dict[str, Any]) -> bool:
    candidate_vintage = candidate.get("vintage") or 0
    current_vintage = current.get("vintage") or 0
    if candidate_vintage != current_vintage:
        return candidate_vintage > current_vintage
    type_rank = {"time_series": 3, "aggregate": 2, "microdata": 1}
    if type_rank.get(candidate.get("dataset_type"), 0) != type_rank.get(current.get("dataset_type"), 0):
        return type_rank.get(candidate.get("dataset_type"), 0) > type_rank.get(current.get("dataset_type"), 0)
    return len(candidate.get("description") or "") > len(current.get("description") or "")


def _catalog() -> list[dict[str, Any]]:
    payload = _catalog_json()
    families: dict[str, dict[str, Any]] = {}
    for raw in payload.get("dataset") or []:
        normalized = _normalize_dataset(raw)
        if not normalized:
            continue
        family_id = normalized["family_id"]
        current = families.get(family_id)
        if current is None or _prefer_dataset(normalized, current):
            families[family_id] = normalized
    return list(families.values())


def _match_score(tokens: list[str], text: str) -> tuple[int, list[str]]:
    lower = str(text or "").lower()
    score = 0
    matched: list[str] = []

    phrase = " ".join(tokens).strip()
    if phrase and phrase in lower:
        score += 10
        matched.append(phrase)

    for token in tokens:
        hits = len(re.findall(rf"\b{re.escape(token)}\b", lower))
        if hits:
            score += min(5, 2 + hits)
            if token not in matched:
                matched.append(token)
            continue
        if token in lower:
            score += 1
            if token not in matched:
                matched.append(token)

    return score, matched


def _dataset_search_score(dataset: dict[str, Any], tokens: list[str]) -> tuple[int, list[str], int]:
    title_score, title_matched = _match_score(tokens, dataset["title_text"])
    description_score, description_matched = _match_score(tokens, dataset["description_text"])
    matched = []
    for term in title_matched + description_matched:
        if term not in matched:
            matched.append(term)

    score = title_score * 3 + description_score + int(dataset.get("economic_bonus") or 0) + int(dataset.get("family_bonus") or 0)
    token_gap = max(0, len(set(tokens)) - len(set(matched)))
    score -= token_gap * 4

    dataset_type = dataset.get("dataset_type")
    if dataset_type == "time_series":
        score += 4
    elif dataset_type == "aggregate":
        score += 2
    elif dataset_type == "microdata":
        score -= 4

    if dataset["family_id"].startswith("timeseries/poverty/"):
        score += 3
    if dataset["family_id"].startswith("timeseries/eits/"):
        score += 3
    if dataset["family_id"].startswith("intltrade/"):
        score += 3
    if dataset["family_id"].startswith("pep/"):
        score += 2

    return score, matched, title_score


def _relevance_label(score: int) -> str:
    if score >= 28:
        return "high"
    if score >= 18:
        return "medium"
    return "neutral"


def _public_dataset(dataset: dict[str, Any], score: int, matched_terms: list[str]) -> dict[str, Any]:
    return {
        "dataset_id": dataset["dataset_id"],
        "family_id": dataset["family_id"],
        "title": dataset["title"],
        "description": dataset["description"],
        "vintage": dataset.get("vintage"),
        "dataset_type": dataset["dataset_type"],
        "market_relevance": _relevance_label(score),
        "matched_terms": matched_terms,
        "api_base_url": dataset.get("api_base_url"),
        "variables_url": dataset.get("variables_url"),
        "geography_url": dataset.get("geography_url"),
        "documentation_url": dataset.get("documentation_url"),
        "examples_url": dataset.get("examples_url"),
        "score": score,
    }


def _load_variables(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    dataset_id = dataset["dataset_id"]
    cached = _variables_cache.get(dataset_id)
    if cached and cached["expires_at"] > _now():
        return cached["value"]

    variables_url = dataset.get("variables_url")
    if not variables_url:
        return []

    response = _session.get(variables_url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    variables = payload.get("variables") or {}
    normalized: list[dict[str, Any]] = []
    for name, metadata in variables.items():
        if metadata.get("predicateOnly"):
            continue
        if name in {"NAME", "GEO_ID"}:
            continue
        label = _clean_label(metadata.get("label"))
        concept = _clean_label(metadata.get("concept"))
        if not label and not concept:
            continue
        normalized.append({
            "name": name,
            "label": label,
            "concept": concept,
            "group": _clean_label(metadata.get("group")),
            "predicate_type": metadata.get("predicateType"),
            "required": bool(metadata.get("required")),
            "search_text": f"{name} {label} {concept} {metadata.get('group') or ''}".lower(),
        })

    _variables_cache[dataset_id] = {
        "expires_at": _now() + VARIABLES_TTL_SECONDS,
        "value": normalized,
    }
    return normalized


def _indicator_suffix_penalty(name: str, label: str) -> int:
    upper = str(name or "").upper()
    if upper.endswith(EXCLUDED_VARIABLE_SUFFIXES):
        return 6
    if "annotation of" in str(label or "").lower():
        return 6
    return 0


def _indicator_search_score(
    dataset: dict[str, Any],
    dataset_score: int,
    variable: dict[str, Any],
    tokens: list[str],
) -> tuple[int, list[str]]:
    base, matched = _match_score(tokens, variable["search_text"])
    score = base
    if not score:
        return 0, []

    score += min(12, dataset_score // 3)
    score += _economic_bonus(variable["search_text"])

    name = str(variable.get("name") or "").upper()
    label = str(variable.get("label") or "")
    if name.endswith("E") or name.endswith("PE"):
        score += 2
    if "estimate" in label.lower():
        score += 1
    predicate_type = str(variable.get("predicate_type") or "").lower()
    if predicate_type in {"int", "float"}:
        score += 3
    if predicate_type in {"string"}:
        score -= 5
    label_lower = label.lower()
    if any(term in label_lower for term in ["code", "flag", "annotation", "identifier", "margin of error", "lower bound", "upper bound", "confidence interval"]):
        score -= 5
    if re.fullmatch(r"[A-Z]{1,4}[0-9]{3,}[A-Z0-9_]*", name):
        score -= 5
    score -= _indicator_suffix_penalty(name, label)
    return max(0, score), matched


def _public_indicator(
    dataset: dict[str, Any],
    dataset_score: int,
    variable: dict[str, Any],
    indicator_score: int,
    matched_terms: list[str],
) -> dict[str, Any]:
    return {
        "indicator_id": f"{dataset['dataset_id']}::{variable['name']}",
        "variable_name": variable["name"],
        "label": variable["label"],
        "concept": variable["concept"],
        "group": variable["group"],
        "predicate_type": variable.get("predicate_type"),
        "required": variable.get("required", False),
        "dataset_id": dataset["dataset_id"],
        "dataset_family_id": dataset["family_id"],
        "dataset_title": dataset["title"],
        "dataset_vintage": dataset.get("vintage"),
        "dataset_type": dataset["dataset_type"],
        "market_relevance": _relevance_label(indicator_score),
        "matched_terms": matched_terms,
        "api_base_url": dataset.get("api_base_url"),
        "variables_url": dataset.get("variables_url"),
        "geography_url": dataset.get("geography_url"),
        "documentation_url": dataset.get("documentation_url"),
        "examples_url": dataset.get("examples_url"),
        "dataset_score": dataset_score,
        "score": indicator_score,
    }


def search_census_metadata(
    query: str | None = None,
    kind: str = "all",
    dataset_limit: int = 8,
    indicator_limit: int = 14,
) -> dict[str, Any]:
    clean_query = str(query or "").strip()
    tokens = _tokenize(clean_query or DEFAULT_DISCOVERY_QUERY)
    featured_mode = not clean_query

    catalog = _catalog()
    scored_datasets: list[tuple[int, list[str], dict[str, Any]]] = []
    for dataset in catalog:
        score, matched_terms, title_score = _dataset_search_score(dataset, tokens)
        if featured_mode:
            if score <= 0:
                continue
        elif (title_score <= 0 and len(matched_terms) < 2) or score <= 0:
            continue
        scored_datasets.append((score, matched_terms, dataset))

    scored_datasets.sort(
        key=lambda row: (
            row[0],
            row[2].get("vintage") or 0,
            row[2].get("dataset_type") == "time_series",
        ),
        reverse=True,
    )

    top_datasets = scored_datasets[: max(1, min(int(dataset_limit), 20))]
    dataset_matches = [_public_dataset(dataset, score, matched_terms) for score, matched_terms, dataset in top_datasets]

    indicator_matches: list[dict[str, Any]] = []
    if kind in {"all", "indicators"} and not featured_mode:
        candidates = top_datasets[:MAX_INDICATOR_DATASETS]
        futures = {}
        with ThreadPoolExecutor(max_workers=min(4, len(candidates) or 1)) as executor:
            for dataset_score, _, dataset in candidates:
                futures[executor.submit(_load_variables, dataset)] = (dataset_score, dataset)

            scored_indicators: list[dict[str, Any]] = []
            for future in as_completed(futures):
                dataset_score, dataset = futures[future]
                try:
                    variables = future.result()
                except Exception:
                    continue
                per_dataset_matches: list[dict[str, Any]] = []
                for variable in variables:
                    indicator_score, matched_terms = _indicator_search_score(dataset, dataset_score, variable, tokens)
                    if indicator_score <= 0:
                        continue
                    per_dataset_matches.append(_public_indicator(dataset, dataset_score, variable, indicator_score, matched_terms))

                per_dataset_matches.sort(
                    key=lambda item: (item["score"], item["dataset_score"]),
                    reverse=True,
                )
                scored_indicators.extend(per_dataset_matches[: max(3, min(8, indicator_limit))])

        scored_indicators.sort(
            key=lambda item: (
                item["score"],
                item["dataset_score"],
                item.get("dataset_vintage") or 0,
            ),
            reverse=True,
        )
        indicator_matches = scored_indicators[: max(1, min(int(indicator_limit), 40))]

    return {
        "status": "ok",
        "source": "census_public_metadata",
        "query": clean_query,
        "kind": kind,
        "mode": "featured" if featured_mode else "search",
        "metadata_access": {
            "api_key_required": False,
            "data_queries_require_api_key": True,
        },
        "featured_queries": FEATURED_QUERIES,
        "dataset_matches": [] if kind == "indicators" else dataset_matches,
        "indicator_matches": [] if kind == "datasets" else indicator_matches,
        "datasets_scanned": len(catalog),
        "datasets_considered_for_indicators": [
            dataset["dataset_id"]
            for _, _, dataset in top_datasets[:MAX_INDICATOR_DATASETS]
        ],
    }
