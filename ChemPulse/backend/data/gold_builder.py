from __future__ import annotations

from pathlib import Path

from backend.data.schemas import GOLD_SCHEMA_SQL
from backend.config import get_config
from backend.data.db import get_connection
from backend.data.scaffold_registry import ScaffoldRegistry

def build_gold_layer(db_path: str | Path | None = None) -> Path:
    final_path = Path(db_path) if db_path else get_config().database_path
    final_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(read_only=False) as con:
        con.execute(GOLD_SCHEMA_SQL)
    ScaffoldRegistry.upsert_seed_scaffolds()
    return final_path


if __name__ == "__main__":
    path = build_gold_layer()
    print(f"Gold layer built successfully at {path}")
