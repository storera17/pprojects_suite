from __future__ import annotations

from backend.data.gold_builder import build_gold_layer
from backend.services.chemical_space_service import ChemicalSpaceService
from backend.services.scaffold_service import ScaffoldService


def test_amino_acids_load_as_individual_scaffolds(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    build_gold_layer()

    names = {row["name"] for row in ScaffoldService.list_registered_scaffolds(query="amino acid")}

    assert "Amino acid" not in names
    assert {
        "Glycine",
        "Alanine",
        "Valine",
        "Leucine",
        "Isoleucine",
        "Serine",
        "Threonine",
        "Cysteine",
        "Methionine",
        "Phenylalanine",
        "Tyrosine",
        "Tryptophan",
        "Aspartic acid",
        "Glutamic acid",
        "Asparagine",
        "Glutamine",
        "Lysine",
        "Arginine",
        "Histidine",
        "Proline",
    }.issubset(names)


def test_requested_scaffold_families_load(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    build_gold_layer()

    names = {row["name"] for row in ScaffoldService.list_registered_scaffolds()}

    assert {"Ethylene glycol", "Monoglyme", "Diglyme", "Paclitaxel taxane core"}.issubset(names)
    assert {"Gallic acid", "Ellagic acid", "Gallotannin phenolic core"}.issubset(names)


def test_invalid_smiles_is_rejected_safely(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    build_gold_layer()

    result = ScaffoldService.add_scaffold_by_smiles("Broken scaffold", "Manual", "Manual", "C1CC")

    assert result["ok"] is False
    assert "Invalid SMILES" in result["error"]


def test_visualization_services_return_new_scaffold_families(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    build_gold_layer()

    amino_rows = ScaffoldService.search_scaffolds("glycine", limit=5)
    polyether_points = ChemicalSpaceService.search_galaxy_points("ethylene glycol")
    tannin_points = ChemicalSpaceService.search_galaxy_points("tannin")

    assert amino_rows[0]["name"] == "Glycine"
    assert {point["scaffold"] for point in polyether_points} >= {"Ethylene glycol"}
    assert {"Gallic acid", "Ellagic acid", "Gallotannin phenolic core"}.intersection(
        {point["scaffold"] for point in tannin_points}
    )
