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
    
    
    @property
    def api_base_url(self) -> str:
        configured = os.getenv("CHEMPULSE_API_BASE_URL", "").strip()
        if configured:
            return configured.rstrip("/")
        backend_port = os.getenv("BACKEND_PORT", "8000").strip() or "8000"
        return f"http://127.0.0.1:{backend_port}"
    
def get_config() -> AppConfig:
    return AppConfig(project_root=project_root(), storage_dir=storage_dir())

def is_api_key_configured(env_name: str = LITERATURE_API_KEY_ENV) -> bool:
    return bool(get_secret_env(env_name).strip())
