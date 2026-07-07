from __future__ import annotations

from backend.plugins.base import PredictivePlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[PredictivePlugin] = []

    def register(self, plugin: PredictivePlugin) -> None:
        if any(existing.plugin_name == plugin.plugin_name for existing in self._plugins):
            return
        self._plugins.append(plugin)

    def all(self) -> list[PredictivePlugin]:
        return list(self._plugins)

    def run(self, payload: dict) -> list[dict]:
        results: list[dict] = []
        for plugin in self._plugins:
            if plugin.supports(payload):
                results.extend(plugin.predict(payload))
        return results