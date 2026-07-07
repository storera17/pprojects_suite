from __future__ import annotations

from pathlib import Path

import duckdb

from backend.data.synthetic_dataset import SyntheticDatasetConfig, generate_synthetic_dataset


def test_generate_synthetic_dataset_creates_expected_tables(tmp_path: Path) -> None:
    output_path = tmp_path / "synthetic.duckdb"

    summary = generate_synthetic_dataset(
        SyntheticDatasetConfig(
            output_path=output_path,
            rows=1000,
            scaffold_count=50,
            cluster_count=12,
            publication_count=120,
        )
    )

    assert output_path.exists()
    assert summary["rows"]["gold_galaxy_points"] == 1000
    assert summary["rows"]["gold_scaffold_stats"] == 50
    assert summary["rows"]["scaffold_entries"] == 50
    assert summary["rows"]["bronze_core_publications"] == 120

    with duckdb.connect(str(output_path), read_only=True) as con:
        assert con.execute("SELECT COUNT(DISTINCT cluster_id) FROM gold_galaxy_points").fetchone()[0] == 12
        assert con.execute("SELECT COUNT(*) FROM core_ingestion_runs").fetchone()[0] == 1