from __future__ import annotations

from typing import Any

from backend.plugins.base import PredictivePlugin
from backend.plugins.registry import PluginRegistry


class EchoPlugin(PredictivePlugin):
    plugin_name = "echo"

    def supports(self, payload: dict[str, Any]) -> bool:
        return payload.get("enabled", False)

    def predict(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"title": payload["title"]}]


def test_registry_runs_supported_plugins() -> None:
    registry = PluginRegistry()
    registry.register(EchoPlugin())

    assert registry.run({"enabled": True, "title": "Signal"}) == [{"title": "Signal"}]
    assert registry.run({"enabled": False, "title": "Signal"}) == []


def test_registry_ignores_duplicate_plugin_names() -> None:
    registry = PluginRegistry()
    registry.register(EchoPlugin())
    registry.register(EchoPlugin())

    assert len(registry.all()) == 1
