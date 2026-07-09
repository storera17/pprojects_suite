from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from backend.core.paths import storage_dir
from backend.search.search_common import metadata, safe_float


REFERENCE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "canonical_query": "benzene",
        "aliases": ("benzene", "phenyl scaffold", "arene benzene"),
        "offers": (
            {"provider": "reference_supplier_alpha", "provider_display_name": "Reference Supplier Alpha", "catalog_id": "REF-BEN-001", "package_size": 25.0, "package_unit": "g", "currency": "USD", "price": 42.5, "availability": "In stock", "lead_time_days": 2},
            {"provider": "reference_supplier_beta", "provider_display_name": "Reference Supplier Beta", "catalog_id": "REF-BEN-014", "package_size": 100.0, "package_unit": "g", "currency": "USD", "price": 129.0, "availability": "Low stock", "lead_time_days": 4},
        ),
    },
    {
        "canonical_query": "caffeine",
        "aliases": ("caffeine", "trimethylxanthine"),
        "offers": (
            {"provider": "reference_supplier_alpha", "provider_display_name": "Reference Supplier Alpha", "catalog_id": "REF-CAF-009", "package_size": 10.0, "package_unit": "g", "currency": "USD", "price": 31.0, "availability": "In stock", "lead_time_days": 2},
            {"provider": "reference_supplier_gamma", "provider_display_name": "Reference Supplier Gamma", "catalog_id": "REF-CAF-122", "package_size": 50.0, "package_unit": "g", "currency": "USD", "price": 118.0, "availability": "Made to order", "lead_time_days": 7},
        ),
    },
    {
        "canonical_query": "quinoline scaffold",
        "aliases": ("quinoline", "quinoline scaffold", "heteroaromatic quinoline"),
        "offers": (
            {"provider": "reference_supplier_beta", "provider_display_name": "Reference Supplier Beta", "catalog_id": "REF-QUI-102", "package_size": 5.0, "package_unit": "g", "currency": "USD", "price": 74.0, "availability": "In stock", "lead_time_days": 3},
            {"provider": "reference_supplier_gamma", "provider_display_name": "Reference Supplier Gamma", "catalog_id": "REF-QUI-311", "package_size": 25.0, "package_unit": "g", "currency": "USD", "price": 302.0, "availability": "Backorder", "lead_time_days": 10},
        ),
    },
)


@dataclass(frozen=True)
class PricingProvider:
    provider: str
    display_name: str
    enabled: bool
    compliance_mode: str
    detail: str

    def compare(self, normalized_query: str, quantity: float, unit: str, region: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def descriptor(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "compliance_mode": self.compliance_mode,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ReferenceCatalogProvider(PricingProvider):
    def compare(self, normalized_query: str, quantity: float, unit: str, region: str) -> list[dict[str, Any]]:
        matched = _match_reference_catalog(normalized_query)
        if not matched:
            return []
        captured_at = _now()
        offers: list[dict[str, Any]] = []
        for entry in matched["offers"]:
            normalized_unit_price = _normalize_unit_price(
                price=safe_float(entry["price"], 0.0),
                package_size=safe_float(entry["package_size"], 1.0),
            )
            offers.append(
                {
                    **entry,
                    "compound_name": matched["canonical_query"].title(),
                    "requested_quantity": quantity,
                    "requested_unit": unit,
                    "region": region,
                    "captured_at": captured_at,
                    "normalized_unit_price": normalized_unit_price,
                    "normalized_unit": f"{entry['currency']}/{entry['package_unit']}",
                    "compliance_status": "reference_demo_data",
                    "warning": "Reference demo data only. Enable a licensed supplier feed before using for procurement.",
                }
            )
        return offers


@dataclass(frozen=True)
class DisabledProviderStub(PricingProvider):
    def compare(self, normalized_query: str, quantity: float, unit: str, region: str) -> list[dict[str, Any]]:
        return []


class PricingService:
    """Normalize supplier comparisons while keeping compliance visible."""

    PROVIDERS: tuple[PricingProvider, ...] = (
        ReferenceCatalogProvider(
            provider="reference_catalog",
            display_name="ChemPulse Reference Catalog",
            enabled=True,
            compliance_mode="sample_data",
            detail="Local reference offers for UI and contract testing. Not live procurement pricing.",
        ),
        DisabledProviderStub(
            provider="licensed_supplier_feed",
            display_name="Licensed Supplier Feed",
            enabled=False,
            compliance_mode="blocked_pending_terms_review",
            detail="Disabled until a licensed source, terms review, and storage policy are approved.",
        ),
    )

    @classmethod
    def compare(cls, payload: dict[str, Any]) -> dict[str, Any]:
        query = str(payload.get("query") or "").strip()
        normalized_query = _normalize_query(query)
        quantity = max(safe_float(payload.get("quantity") or 1.0, 1.0), 0.01)
        unit = str(payload.get("unit") or "g").strip() or "g"
        region = str(payload.get("region") or "US").strip().upper() or "US"
        record_snapshot = bool(payload.get("record_snapshot", False))

        if not normalized_query:
            return {
                "query": {
                    "raw_query": query,
                    "normalized_query": "",
                    "quantity": quantity,
                    "unit": unit,
                    "region": region,
                },
                "offers": [],
                "providers": [provider.descriptor() for provider in cls.PROVIDERS],
                "warnings": ["Enter a structure, scaffold, or supplier query before comparing prices."],
                "metadata": metadata(0, "pricing_service", "Enter a structure, scaffold, or supplier query before comparing prices."),
            }

        offers: list[dict[str, Any]] = []
        warnings: list[str] = []
        for provider in cls.PROVIDERS:
            if not provider.enabled:
                warnings.append(f"{provider.display_name} is disabled: {provider.detail}")
                continue
            offers.extend(provider.compare(normalized_query, quantity, unit, region))

        offers.sort(key=lambda offer: (safe_float(offer.get("normalized_unit_price"), 0.0), safe_float(offer.get("price"), 0.0)))
        response = {
            "query": {
                "raw_query": query,
                "normalized_query": normalized_query,
                "quantity": quantity,
                "unit": unit,
                "region": region,
            },
            "offers": offers,
            "providers": [provider.descriptor() for provider in cls.PROVIDERS],
            "warnings": warnings,
            "metadata": {
                **metadata(
                    len(offers),
                    "pricing_service",
                    "No enabled supplier feeds returned offers for that query. Reference demo data covers only a small seed catalog."
                    if not offers
                    else "",
                ),
                "source_count": len({offer["provider"] for offer in offers}),
                "freshness": "daily snapshot target; current refresh is manual until provider automation is approved",
            },
        }
        if record_snapshot:
            _append_history_snapshot(response)
        return response

    @classmethod
    def history(cls, payload: dict[str, Any]) -> dict[str, Any]:
        query = _normalize_query(str(payload.get("query") or payload.get("q") or "").strip())
        items = _read_json(_history_path(), default=[])
        if query:
            items = [item for item in items if item.get("query", {}).get("normalized_query") == query]
        items = sorted(items, key=lambda item: str(item.get("captured_at") or ""), reverse=True)
        return {
            "items": items[:25],
            "metadata": {
                **metadata(
                    min(len(items), 25),
                    "pricing_history",
                    "No stored pricing snapshots are available for that query yet.",
                ),
                "source_count": len({offer["provider"] for item in items[:25] for offer in item.get("offers", [])}),
            },
        }

    @classmethod
    def watch(cls, payload: dict[str, Any]) -> dict[str, Any]:
        query = str(payload.get("query") or "").strip()
        normalized_query = _normalize_query(query)
        quantity = max(safe_float(payload.get("quantity") or 1.0, 1.0), 0.01)
        unit = str(payload.get("unit") or "g").strip() or "g"
        cadence = str(payload.get("cadence") or "daily").strip().lower() or "daily"
        if not normalized_query:
            return {
                "items": [],
                "metadata": metadata(0, "pricing_watch", "Enter a query before creating a price watch."),
            }

        watches = _read_json(_watch_path(), default=[])
        watch = {
            "watch_id": f"pricing-watch-{len(watches) + 1:04d}",
            "query": {"raw_query": query, "normalized_query": normalized_query, "quantity": quantity, "unit": unit},
            "cadence": cadence,
            "created_at": _now(),
            "status": "queued_pending_provider_approval",
            "compliance_note": "Daily tracking is queued until a licensed supplier source and retention policy are approved.",
        }
        watches.append(watch)
        _write_json(_watch_path(), watches)
        return {
            "items": [watch],
            "metadata": {
                **metadata(1, "pricing_watch", ""),
                "watch_status": watch["status"],
            },
        }


def _match_reference_catalog(normalized_query: str) -> dict[str, Any] | None:
    for item in REFERENCE_CATALOG:
        aliases = {item["canonical_query"], *item["aliases"]}
        if normalized_query in aliases or any(alias in normalized_query for alias in aliases):
            return item
    return None


def _normalize_query(query: str) -> str:
    return " ".join(str(query or "").lower().replace("-", " ").split())


def _normalize_unit_price(*, price: float, package_size: float) -> float:
    if package_size <= 0:
        return round(price, 4)
    return round(price / package_size, 4)


def _append_history_snapshot(response: dict[str, Any]) -> None:
    if not response.get("offers"):
        return
    snapshots = _read_json(_history_path(), default=[])
    offers = response["offers"]
    best_offer = offers[0]
    snapshots.append(
        {
            "snapshot_id": f"pricing-snapshot-{len(snapshots) + 1:04d}",
            "captured_at": best_offer.get("captured_at", _now()),
            "query": response["query"],
            "offers": offers,
            "best_offer": {
                "provider": best_offer.get("provider_display_name"),
                "catalog_id": best_offer.get("catalog_id"),
                "normalized_unit_price": best_offer.get("normalized_unit_price"),
                "normalized_unit": best_offer.get("normalized_unit"),
            },
        }
    )
    _write_json(_history_path(), snapshots[-100:])


def _history_path() -> Path:
    return storage_dir() / "pricing-history.json"


def _watch_path() -> Path:
    return storage_dir() / "pricing-watch.json"


def _read_json(path: Path, *, default: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not path.exists():
        return default
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
    return parsed if isinstance(parsed, list) else default


def _write_json(path: Path, payload: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
