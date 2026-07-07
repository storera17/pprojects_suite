from __future__ import annotations

from backend.data.core_publication_repository import CorePublicationRepository, ensure_core_ingestion_schema
from backend.data.db import get_connection, initialize_schema
from backend.data.repository import GoldRepository
from backend.data.scaffold_publication_matcher import refresh_scaffold_matches
from backend.services.chemical_space_service import ChemicalSpaceService


def test_scaffold_matcher_rebuilds_galaxy_from_publication_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CHEMPULSE_STORAGE_DIR", str(tmp_path))
    scaffold_file = tmp_path / "scaffolds.txt"
    scaffold_file.write_text(
        "\n".join(
            [
                "1-10: Test scaffolds",
                "Benzene",
                "Indole",
                "Pyridine",
            ]
        ),
        encoding="utf-8",
    )
    initialize_schema()
    ensure_core_ingestion_schema()
    with get_connection(read_only=False) as con:
        con.execute("INSERT INTO gold_scaffold_stats VALUES ('Old Demo', 99, '', 'Demo', 0)")
        con.execute("INSERT INTO gold_galaxy_points VALUES ('old_demo', 0, 0, 0, 'old', 'Old Demo', 0)")

    CorePublicationRepository.upsert_publications(
        [
            {
                "core_id": "core-1",
                "title": "Benzene and indole chemistry",
                "doi": "10.1000/benzene",
                "year_published": 2026,
                "published_date": "2026-05-21",
                "authors": ["Ada Chemist"],
                "journal": "Journal of Useful Chemistry",
                "abstract": "This paper studies benzene selectivity.",
                "topics": ["organic chemistry"],
                "full_text_url": None,
                "source_url": None,
                "raw": {"id": "core-1"},
            }
        ],
        "chemistry",
    )

    result = refresh_scaffold_matches(scaffold_file)
    points = GoldRepository.galaxy_points()
    labels = list(ChemicalSpaceService.build_galaxy_figure(points).data[0].text)

    assert result.matched_scaffolds == 2
    assert {point["scaffold"] for point in points} == {"Benzene", "Indole"}
    assert labels == ["Benzene", "Indole"]
