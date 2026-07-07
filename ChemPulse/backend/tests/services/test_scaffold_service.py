from __future__ import annotations

from backend.data.db import get_connection, initialize_schema
from backend.services.chemical_space_service import ChemicalSpaceService
from backend.services.predictive_lab_service import PredictiveLabService
from backend.services.research_pulse_service import ResearchPulseService
from backend.services.scaffold_service import ScaffoldService


def _seed_live_scaffold_evidence() -> None:
    initialize_schema()
    with get_connection(read_only=False) as con:
        con.execute("INSERT INTO gold_scaffold_stats VALUES ('Benzene', 2, '10.1000/benzene', 'Journal Scheduler', 0)")
        con.execute("INSERT INTO gold_galaxy_points VALUES ('benzene', 0, 0, 0, 'cluster_live', 'Benzene', 0)")


def test_cluster_selection_updates_scaffold_and_source_slices(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_live_scaffold_evidence()

    scaffolds = ScaffoldService.get_top_scaffolds_for_cluster(["cluster_live"])
    funding = ScaffoldService.get_funding_slices_for_cluster(["cluster_live"])

    assert scaffolds[0]["name"] == "Benzene"
    assert scaffolds[0]["count"] == 1
    assert funding[0]["label"] == "Journal Scheduler"
    assert funding[0]["value"] == "$0"


def test_scaffold_search_and_research_pulse_use_live_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_live_scaffold_evidence()

    scaffolds = ScaffoldService.search_scaffolds("scheduler")
    pulse = ResearchPulseService.get_pulse(search_query="benzene")

    assert scaffolds[0]["top_funder"] == "Journal Scheduler"
    assert pulse[0]["tag"] == "Search focus"
    assert "Benzene" in pulse[0]["title"]


def test_search_filters_galaxy_points_and_predictive_insights(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_live_scaffold_evidence()

    points = ChemicalSpaceService.search_galaxy_points("benzene")
    insights = PredictiveLabService.get_insights_for_search("benzene")

    assert {point["scaffold"] for point in points} == {"Benzene"}
    assert len(insights) == 2
    assert all("Benzene" in insight["title"] for insight in insights)
    assert all(insight["top_funder"] == "Journal Scheduler" for insight in insights)

