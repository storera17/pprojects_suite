
from abc import ABC, abstractmethod
from typing import Any


class PredictivePlugin(ABC):
    plugin_name: str = "base"
    plugin_version: str = "0.1.0"

    @abstractmethod
    def supports(self, payload: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def predict(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError