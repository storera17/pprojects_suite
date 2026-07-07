from __future__ import annotations

from backend.data.db import get_connection, initialize_schema, is_transient_duckdb_error
from backend.data.gold_builder import build_gold_layer
from backend.data.repository import GoldRepository


def test_gold_layer_initializes_without_demo_dashboard_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    build_gold_layer()

    assert GoldRepository.top_scaffolds(limit=3) == []
    assert GoldRepository.funding_slices_for_clusters(["cluster_12"]) == []
    assert GoldRepository.overview_metrics()["total_documents"] == 0
    assert GoldRepository.galaxy_points() == []


def test_gold_repository_searches_live_scaffolds_by_name_and_source(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    initialize_schema()
    with get_connection(read_only=False) as con:
        con.execute("INSERT INTO gold_scaffold_stats VALUES ('Benzene', 2, '10.1000/benzene', 'Journal of Useful Chemistry', 0)")
        con.execute("INSERT INTO gold_galaxy_points VALUES ('benzene', 0, 0, 0, 'cluster_live', 'Benzene', 0)")

    by_name = GoldRepository.search_scaffolds("benzene")
    by_source = GoldRepository.search_scaffolds("useful")

    assert by_name[0]["name"] == "Benzene"
    assert by_source[0]["top_funder"] == "Journal of Useful Chemistry"


def test_duckdb_unique_file_handle_conflict_is_transient() -> None:
    error = RuntimeError(
        'Binder Error: Unique file handle conflict: Cannot attach "chempulse" - '
        'the database file "C:\\Users\\andy_\\Desktop\\chempulse_repo\\storage\\chempulse.duckdb" '
        'is already attached by database "chempulse"'
    )

    assert is_transient_duckdb_error(error) is True


def test_database_connection_uses_lock_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))

    with get_connection(read_only=False) as con:
        con.execute("SELECT 1").fetchone()

    assert (tmp_path / "chempulse.duckdb.lock").exists()
