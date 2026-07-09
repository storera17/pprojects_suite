from __future__ import annotations

from backend.services.pricing_service import PricingService


def test_compare_normalizes_reference_offers(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    payload = PricingService.compare({"query": "quinoline scaffold", "quantity": 5, "unit": "g", "record_snapshot": True})

    assert payload["offers"]
    assert payload["offers"][0]["normalized_unit_price"] <= payload["offers"][-1]["normalized_unit_price"]
    assert payload["query"]["normalized_query"] == "quinoline scaffold"
    assert payload["metadata"]["source_count"] >= 1


def test_compare_surfaces_disabled_provider_and_empty_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    payload = PricingService.compare({"query": "unknown sample", "quantity": 1, "unit": "g"})

    assert payload["offers"] == []
    assert payload["warnings"]
    assert any(provider["provider"] == "licensed_supplier_feed" and not provider["enabled"] for provider in payload["providers"])
    assert payload["metadata"]["empty_state_reason"]


def test_watch_and_history_persist(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    watch_payload = PricingService.watch({"query": "benzene", "quantity": 25, "unit": "g", "cadence": "daily"})
    PricingService.compare({"query": "benzene", "quantity": 25, "unit": "g", "record_snapshot": True})
    history_payload = PricingService.history({"query": "benzene"})

    assert watch_payload["items"][0]["status"] == "queued_pending_provider_approval"
    assert history_payload["items"]
    assert history_payload["items"][0]["best_offer"]["provider"]
