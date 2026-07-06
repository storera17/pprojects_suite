from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from backend.core.constants import LITERATURE_API_KEY_ENV
from backend.core.env import get_env_value
from backend.core.paths import project_root, storage_dir

@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    storage_dir: Path
    database_filename: str = "chempulse.duckdb"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    literature_api_key_env: str = LITERATURE_API_KEY_ENV

    @property
    def database_path(self) -> Path:
        return self.storage_dir / self.database_filename
    
    @property
    def literature_api_key(self) -> str:
        return get_secret_env(self.literature_api_key_env)
    
    @property
    def literature_api_key_configured(self) -> bool:
        return is_api_key_configured(self.literature_api_key_env)