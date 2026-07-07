from __future__ import annotations

from rdkit import Chem
from starlette.testclient import TestClient

from app import app
from backend.data.core_publication_repository import CorePublicationRepository
from backend.services.scaffold_service import ScaffoldService


def test_existing_major_endpoints_remain_available() -> None:
    client = TestClient(app._api)
    routes = [
        "/api/documents",
        "/api/journals",
        "/api/publications",
        "/api/scaffolds",
        "/api/galaxy/points",
        "/api/analytics/top-scaffolds",
        "/api/analytics/journal-publications",
        "/api/research-pulse",
        "/api/publication-radar",
        "/api/predictive-lab/status",
        "/api/status",
    ]

    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, route
        assert response.text.strip(), route


def test_chemical_intelligence_routes_are_registered() -> None:
    route_paths = {getattr(route, "path", "") for route in app._api.routes}

    assert "/api/search/literature" in route_paths
    assert "/api/search/structure" in route_paths
    assert "/api/search/reaction" in route_paths
    assert "/api/search/reaction-name" in route_paths
    assert "/api/mechanism/explain" in route_paths
    assert "/api/reports/reaction" in route_paths
    assert "/chempulse/api/search/literature" in route_paths


def test_topic_search_returns_local_literature_records(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post("/api/search/literature", json={"query": "esterification aspirin scaffold"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["metadata"]["record_count"] >= 1
    assert payload["items"][0]["publication_id"] == "chem-intel-1"
    assert "highlighted_snippets" in payload["items"][0]


def test_empty_topic_search_returns_structured_empty_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = TestClient(app._api)

    response = client.post("/api/search/literature", json={"query": ""})
    payload = response.json()

    assert response.status_code == 200
    assert payload["items"] == []
    assert payload["metadata"]["empty_state_reason"]


def test_valid_smiles_structure_search_canonicalizes_and_matches(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post("/api/search/structure", json={"smiles": "c1ccccc1", "mode": "exact", "role": "scaffold"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["query"]["canonical_smiles"] == "c1ccccc1"
    assert payload["matches"]
    assert payload["matches"][0]["match_type"] == "exact"


def test_backend_accepts_drawn_molblock_and_canonicalizes(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)
    molblock = _molblock_from_smiles("c1ccccc1")

    response = client.post("/api/search/structure", json={"molblock": molblock, "mode": "exact", "role": "scaffold"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["query"]["input_format"] == "molblock"
    assert payload["query"]["canonical_smiles"] == "c1ccccc1"
    assert payload["matches"]


def test_invalid_smiles_returns_safe_validation_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = TestClient(app._api)

    response = client.post("/api/search/structure", json={"smiles": "not-a-smiles"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["matches"] == []
    assert "Invalid structure" in payload["validation_error"]


def test_invalid_drawn_molblock_returns_validation_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = TestClient(app._api)

    response = client.post("/api/search/structure", json={"molblock": "ChemPulse sketch\nbroken\nM  END"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["matches"] == []
    assert "Invalid structure" in payload["validation_error"]


def test_substructure_search_works_when_rdkit_supported(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post("/api/search/structure", json={"smiles": "c1ccccc1", "mode": "substructure", "role": "scaffold"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["matches"]
    assert payload["matches"][0]["match_type"] in {"substructure", "exact"}


def test_drawn_substrate_search_returns_seeded_matches(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post(
        "/api/search/structure",
        json={"molblock": _molblock_from_smiles("c1ccccc1"), "mode": "exact", "role": "substrate"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["matches"]
    assert payload["matches"][0]["role"] == "substrate"


def test_drawn_product_search_returns_seeded_matches(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post(
        "/api/search/structure",
        json={"molblock": _molblock_from_smiles("c1ccccc1"), "mode": "exact", "role": "product"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["matches"]
    assert payload["matches"][0]["role"] == "product"


def test_empty_structure_search_results_are_structured(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post("/api/search/structure", json={"smiles": "C", "mode": "exact", "role": "scaffold"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["matches"] == []
    assert payload["metadata"]["empty_state_reason"]


def test_reaction_search_returns_candidate_matches(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post(
        "/api/search/reaction",
        json={
            "substrate": "CC(=O)O",
            "product": "CC(=O)OC",
            "catalyst": "O",
            "mechanism_hint": "esterification acyl transfer",
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["candidate_reactions"]
    assert payload["matched_publications"]
    assert "confidence" in payload["candidate_reactions"][0]
    assert "validated_inputs" in payload


def test_reaction_name_search_matches_seeded_families_and_aliases(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post("/api/search/reaction-name", json={"query": "Suzuki coupling"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["items"]
    assert payload["items"][0]["name"] == "Suzuki cross-coupling"
    assert "Suzuki coupling" in payload["items"][0]["aliases"]


def test_fuzzy_reaction_name_search_works_on_aliases(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = TestClient(app._api)

    response = client.post("/api/search/reaction-name", json={"query": "Diels Alder"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["items"]
    assert payload["items"][0]["name"] == "Diels-Alder cycloaddition"


def test_drawn_reaction_structures_are_validated_by_role(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post(
        "/api/search/reaction",
        json={
            "reaction_name": "Suzuki coupling",
            "substrate": [{"molblock": _molblock_from_smiles("c1ccccc1Br"), "input_format": "molblock"}],
            "product": [{"molblock": _molblock_from_smiles("c1ccccc1-c1ccccc1"), "input_format": "molblock"}],
            "catalyst": [{"molblock": _molblock_from_smiles("Cl[Pd]Cl"), "input_format": "molblock"}],
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["validated_inputs"]["substrate"][0]["input_format"] == "molblock"
    assert payload["validated_inputs"]["substrate"][0]["canonical_smiles"]
    assert payload["candidate_reactions"][0]["mechanism_name"] == "Suzuki cross-coupling"
    assert payload["candidate_reactions"][0]["matched_substrates"]


def test_invalid_drawn_reaction_structure_returns_safe_validation_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = TestClient(app._api)

    response = client.post(
        "/api/search/reaction",
        json={"reaction_name": "SN2", "substrate": [{"molblock": "ChemPulse sketch\nbroken\nM  END", "input_format": "molblock"}]},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["validation_errors"]
    assert "Invalid structure" in payload["validation_errors"][0]
    assert payload["warnings"]


def test_combined_drawn_structure_and_reaction_name_ranks_candidates(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post(
        "/api/search/reaction",
        json={
            "reaction_name": "Friedel-Crafts acylation",
            "substrate": [{"molblock": _molblock_from_smiles("c1ccccc1"), "input_format": "molblock"}],
            "product": [{"molblock": _molblock_from_smiles("CC(=O)c1ccccc1"), "input_format": "molblock"}],
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["candidate_reactions"]
    assert payload["candidate_reactions"][0]["mechanism_name"] == "Friedel-Crafts acylation"
    assert payload["candidate_reactions"][0]["matched_aliases"]


def test_selected_candidate_can_request_mechanism_explanation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post(
        "/api/mechanism/explain",
        json={
            "reaction_name": "SN2",
            "substrate": [{"molblock": _molblock_from_smiles("CCBr"), "input_format": "molblock"}],
            "product": [{"molblock": _molblock_from_smiles("CCO"), "input_format": "molblock"}],
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["steps"]
    assert payload["confidence"] >= 0
    assert "warnings" in payload


def test_mechanism_explanation_includes_evidence_confidence_and_warnings(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post("/api/mechanism/explain", json={"mechanism_hint": "esterification", "substrate": "CC(=O)O", "product": "CC(=O)OC"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["steps"]
    assert "evidence" in payload
    assert isinstance(payload["confidence"], float)
    assert "metadata" in payload


def test_low_confidence_mechanism_does_not_fake_certainty(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    client = TestClient(app._api)

    response = client.post("/api/mechanism/explain", json={"mechanism_hint": "unknown transformation"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["confidence"] < 0.5
    assert payload["warnings"]


def test_report_generation_includes_matched_literature_citations(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    _seed_chemical_intelligence_records()
    client = TestClient(app._api)

    response = client.post(
        "/api/reports/reaction",
        json={"mechanism_hint": "esterification acyl transfer", "substrate": "CC(=O)O", "product": "CC(=O)OC"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["report_id"].startswith("reaction-report-")
    assert "# ChemPulse Explained Reaction Report" in payload["markdown"]
    assert payload["citations"]
    assert "chem-intel-1" in payload["markdown"]


def test_chemical_intelligence_page_mounts() -> None:
    assert "chemical-intelligence" in app._unevaluated_pages
    page = app._unevaluated_pages["chemical-intelligence"]
    assert page.title == "ChemPulse Chemical Intelligence"


def test_structure_search_page_includes_drawer_and_serialization_adapter() -> None:
    from frontend.ui.pages.chemical_intelligence import _chemical_intelligence_markup, _chemical_intelligence_script

    markup = _chemical_intelligence_markup()
    script = _chemical_intelligence_script()

    assert "Draw Structure" in markup
    assert "Paste SMILES" in markup
    assert "Paste MolBlock" in markup
    assert 'id="cp-ci-sketcher"' in markup
    assert "molblockFromSketch" in script
    assert 'payload.molblock = molblockFromSketch()' in script


def test_reaction_search_page_is_draw_first_with_advanced_fallback() -> None:
    from frontend.ui.pages.chemical_intelligence import _chemical_intelligence_markup, _chemical_intelligence_script

    markup = _chemical_intelligence_markup()
    script = _chemical_intelligence_script()

    assert "Reaction Search" in markup
    assert 'id="cp-ci-reaction-sketcher"' in markup
    assert "Add substrate" in markup
    assert "Add product" in markup
    assert "Add catalyst" in markup
    assert "Search by Reaction Name" in markup
    assert "Advanced SMILES/MolBlock fallback" in markup
    assert "/api/search/reaction-name" in script
    assert "reactionSlots" in script
    assert "molblockFromState(reactionSketch)" in script


def _seed_chemical_intelligence_records() -> None:
    ScaffoldService.add_scaffold_by_smiles("Benzene CI", "Aromatic scaffold", "Arenes", "c1ccccc1")
    CorePublicationRepository.upsert_publications(
        [
            {
                "core_id": "chem-intel-1",
                "title": "Aspirin esterification scaffold mechanism with acyl transfer",
                "doi": "10.1000/chem-intel",
                "year_published": 2026,
                "published_date": "2026-01-01",
                "authors": ["Ada Chemist"],
                "journal": "Journal of Local Chemical Intelligence",
                "abstract": "This local record discusses esterification, acyl transfer, benzene scaffold evidence, and reaction mechanism reasoning.",
                "topics": ["esterification", "scaffold", "mechanism", "benzene"],
                "full_text_url": None,
                "source_url": None,
                "raw": {"id": "chem-intel-1"},
            }
        ],
        "esterification scaffold",
    )


def _molblock_from_smiles(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None
    return Chem.MolToMolBlock(mol)
