from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import json

import duckdb

from backend.core.paths import storage_dir
from backend.data.schemas import CORE_INGESTION_SCHEMA_SQL, GOLD_SCHEMA_SQL

DEFAULT_SYNTHETIC_ROWS = 1_000_000
DEFAULT_SCAFFOLD_COUNT = 5_000
DEFAULT_CLUSTER_COUNT = 240
DEFAULT_PUBLICATION_COUNT = 120_000

@dataclass(frozen=True)
class SyntheticDatasetConfig:
    output_path: Path
    rows: int = DEFAULT_SYNTHETIC_ROWS
    scaffold_count: int = DEFAULT_SCAFFOLD_COUNT
    cluster_count: int = DEFAULT_CLUSTER_COUNT
    publication_count: int = DEFAULT_PUBLICATION_COUNT

def default_output_path(filename: str = "chempulse-synthetic-1m.duckdb") -> Path:
    return storage_dir() / "datasets" / filename

def generate_synthetic_dataset(config: SyntheticDatasetConfig | None = None) -> dict[str, Any]:
    config = config or SyntheticDatasetConfig(output_path=default_output_path())
    if config.rows <= 0:
        raise ValueError("rows must be greater than zero")
    if config.scaffold_count <= 0 or config.cluster_count <= 0 or config.publication_count <= 0:
        raise ValueError("scaffold_count, cluster_count, and publication_count must be greater than zero")

    output_path = config.output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(output_path)) as con:
        _create_schema(con)
        _populate_scaffolds(con, config.scaffold_count)
        _populate_galaxy_points(con, config.rows, config.scaffold_count, config.cluster_count)
        _populate_publications(con, config.publication_count, config.scaffold_count)
        _populate_ingestion_runs(con)
        _populate_payloads(con, config.rows, config.publication_count)

        summary = {
            "path": str(output_path),
            "rows": {
                "gold_galaxy_points": _count_rows(con, "gold_galaxy_points"),
                "gold_scaffold_stats": _count_rows(con, "gold_scaffold_stats"),
                "scaffold_entries": _count_rows(con, "scaffold_entries"),
                "bronze_core_publications": _count_rows(con, "bronze_core_publications"),
                "core_ingestion_runs": _count_rows(con, "core_ingestion_runs"),
                "chempulse_payloads": _count_rows(con, "chempulse_payloads"),
            },
        }

    return summary

def _create_schema(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(GOLD_SCHEMA_SQL)
    con.execute(CORE_INGESTION_SCHEMA_SQL)
    con.execute("DELETE FROM gold_scaffold_stats")
    con.execute("DELETE FROM gold_galaxy_points")
    con.execute("DELETE FROM scaffold_entries")
    con.execute("DELETE FROM bronze_core_publications")
    con.execute("DELETE FROM core_ingestion_runs")
    con.execute("DELETE FROM core_ingestion_cursors")
    con.execute("DELETE FROM chempulse_payloads")

def _populate_scaffolds(con: duckdb.DuckDBPyConnection, scaffold_count: int) -> None:
    con.execute(
        """
        INSERT INTO gold_scaffold_stats (scaffold, evidence_count, representative_doi, top_funder, total_funding)
        SELECT
            printf('Scaffold-%05d', i) AS scaffold,
            24 + (i % 500) AS evidence_count,
            printf('10.1000/chempulse.%05d', i) AS representative_doi,
            printf('Journal %02d', i % 48) AS top_funder,
            CAST(150000 + ((i % 240) * 27500) AS DOUBLE) AS total_funding
        FROM range(?) AS series(i)
        """,
        [scaffold_count],
    )
    con.execute(
        """
        INSERT INTO scaffold_entries (name, category, family, canonical_smiles, source, status, created_at, updated_at)
        SELECT
            printf('Scaffold-%05d', i) AS name,
            printf('Category %02d', i % 24) AS category,
            printf('Family %02d', i % 36) AS family,
            CASE i % 8
                WHEN 0 THEN 'CCO'
                WHEN 1 THEN 'CCN'
                WHEN 2 THEN 'c1ccccc1'
                WHEN 3 THEN 'CC(=O)O'
                WHEN 4 THEN 'C1CCCCC1'
                WHEN 5 THEN 'CCOC(=O)C'
                WHEN 6 THEN 'NCCO'
                ELSE 'CC(C)O'
            END AS canonical_smiles,
            'synthetic-seed' AS source,
            'active' AS status,
            TIMESTAMP '2025-01-01 00:00:00' AS created_at,
            TIMESTAMP '2026-01-01 00:00:00' AS updated_at
        FROM range(?) AS series(i)
        """,
        [scaffold_count],
    )

def _populate_galaxy_points(
    con: duckdb.DuckDBPyConnection,
    rows: int,
    scaffold_count: int,
    cluster_count: int,
) -> None:
    con.execute(
        """
        INSERT INTO gold_galaxy_points (id, x, y, z, cluster_id, scaffold, funding_usd)
        SELECT
            printf('pt-%07d', i) AS id,
            CAST((((i * 13) % 2000) / 1000.0) - 1.0 AS DOUBLE) AS x,
            CAST((((i * 17) % 2000) / 1000.0) - 1.0 AS DOUBLE) AS y,
            CAST((((i * 19) % 2000) / 1000.0) - 1.0 AS DOUBLE) AS z,
            printf('cluster-%03d', i % ?) AS cluster_id,
            printf('Scaffold-%05d', i % ?) AS scaffold,
            CAST(1000 + ((i % 900) * 175) AS DOUBLE) AS funding_usd
        FROM range(?) AS series(i)
        """,
        [cluster_count, scaffold_count, rows],
    )

def _populate_publications(con: duckdb.DuckDBPyConnection, publication_count: int, scaffold_count: int) -> None:
    con.execute(
        """
        INSERT INTO bronze_core_publications (
            core_id,
            title,
            doi,
            year_published,
            published_date,
            authors_json,
            journal,
            abstract,
            topics_json,
            full_text_url,
            source_url,
            raw_json,
            query,
            fetched_at
        )
        SELECT
            printf('core-%07d', i) AS core_id,
            printf('Synthetic publication %07d for Scaffold-%05d', i, i % ?) AS title,
            printf('10.2000/synthetic.%07d', i) AS doi,
            2016 + (i % 10) AS year_published,
            CAST((DATE '2016-01-01' + CAST(i % 3650 AS INTEGER)) AS VARCHAR) AS published_date,
            printf('["Author %05d","Author %05d"]', i % 50000, (i + 11) % 50000) AS authors_json,
            printf('Journal %02d', i % 48) AS journal,
            printf(
                'Synthetic abstract %07d describing Scaffold-%05d in cluster-%03d with repeatable chemistry evidence.',
                i,
                i % ?,
                i % 240
            ) AS abstract,
            printf('["topic-%02d","topic-%02d"]', i % 32, (i + 7) % 32) AS topics_json,
            printf('https://example.org/fulltext/%07d', i) AS full_text_url,
            printf('https://example.org/source/%07d', i) AS source_url,
            printf('{"synthetic":true,"index":%d}', i) AS raw_json,
            'synthetic dataset' AS query,
            TIMESTAMP '2026-07-01 09:00:00' + ((i % 168) * INTERVAL '1 hour') AS fetched_at
        FROM range(?) AS series(i)
        """,
        [scaffold_count, scaffold_count, publication_count],
    )

def _populate_ingestion_runs(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        INSERT INTO core_ingestion_runs (
            run_id,
            started_at,
            finished_at,
            query,
            initial_query,
            status,
            requested_limit,
            page_size,
            downloaded_count,
            inserted_count,
            updated_count,
            diagnosis_path,
            error_message
        )
        VALUES (
            'synthetic-run-0001',
            TIMESTAMP '2026-07-01 08:00:00',
            TIMESTAMP '2026-07-01 08:18:00',
            'synthetic dataset',
            'synthetic dataset',
            'succeeded',
            5000,
            250,
            5000,
            5000,
            0,
            '',
            NULL
        )
        """
    )
    con.execute(
        """
        INSERT INTO core_ingestion_cursors (source, frontier_core_id, frontier_published_date, query, updated_at, metadata_json)
        VALUES (
            'synthetic',
            'core-0119999',
            '2026-07-01',
            'synthetic dataset',
            TIMESTAMP '2026-07-01 08:18:00',
            '{"synthetic":true}'
        )
        """
    )

def _populate_payloads(con: duckdb.DuckDBPyConnection, rows: int, publication_count: int) -> None:
    payload = {
        "summary": "Synthetic ChemPulse payload for large-scale local testing.",
        "dataset": {
            "gold_galaxy_points": rows,
            "bronze_core_publications": publication_count,
        },
    }
    con.execute(
        """
        INSERT INTO chempulse_payloads (
            payload_id,
            created_at,
            updated_at,
            source,
            status,
            record_count,
            last_error,
            payload_json
        )
        VALUES (?, TIMESTAMP '2026-07-01 08:20:00', TIMESTAMP '2026-07-01 08:20:00', 'synthetic', 'ready', ?, '', ?)
        """,
        ["synthetic-payload-0001", rows, json.dumps(payload, ensure_ascii=True)],
    )

def _count_rows(con: duckdb.DuckDBPyConnection, table_name: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic ChemPulse DuckDB dataset.")
    parser.add_argument("--output", default=str(default_output_path()), help="Output DuckDB path.")
    parser.add_argument("--rows", type=int, default=DEFAULT_SYNTHETIC_ROWS, help="Number of synthetic galaxy rows to generate.")
    parser.add_argument("--scaffolds", type=int, default=DEFAULT_SCAFFOLD_COUNT, help="Number of synthetic scaffolds to generate.")
    parser.add_argument("--clusters", type=int, default=DEFAULT_CLUSTER_COUNT, help="Number of synthetic clusters to generate.")
    parser.add_argument("--publications", type=int, default=DEFAULT_PUBLICATION_COUNT, help="Number of synthetic publications to generate.")
    args = parser.parse_args()

    summary = generate_synthetic_dataset(
        SyntheticDatasetConfig(
            output_path=Path(args.output),
            rows=args.rows,
            scaffold_count=args.scaffolds,
            cluster_count=args.clusters,
            publication_count=args.publications,
        )
    )
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
