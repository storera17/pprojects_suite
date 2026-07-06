"""Purpose: Provide ChemPulse ai functionality in ollama_client.py.
"""

from __future__ import annotations

import requests


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3") -> None:
        self.base_url = base_url
        self.model = model

    def chat(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")