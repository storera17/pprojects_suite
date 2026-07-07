from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any

import duckdb

from backend.chemistry.rdkit_engine import ChemistryEngine
from backend.data.db import get_connection, get_db_path
from backend.data.schemas import GOLD_SCHEMA_SQL

@dataclass(frozen=True)
class ScaffoldSeed:
    name: str
    category: str
    family: str
    smiles: str
    source: str = "seed"
    status: str = "active"

AMINO_ACID_SCAFFOLDS = [
    ScaffoldSeed("Glycine", "Amino acid", "Proteinogenic amino acids", "NCC(=O)O"),
    ScaffoldSeed("Alanine", "Amino acid", "Proteinogenic amino acids", "CC(N)C(=O)O"),
    ScaffoldSeed("Valine", "Amino acid", "Proteinogenic amino acids", "CC(C)C(N)C(=O)O"),
    ScaffoldSeed("Leucine", "Amino acid", "Proteinogenic amino acids", "CC(C)CC(N)C(=O)O"),
    ScaffoldSeed("Isoleucine", "Amino acid", "Proteinogenic amino acids", "CCC(C)C(N)C(=O)O"),
    ScaffoldSeed("Serine", "Amino acid", "Proteinogenic amino acids", "N[C@@H](CO)C(=O)O"),
    ScaffoldSeed("Threonine", "Amino acid", "Proteinogenic amino acids", "C[C@H](O)[C@H](N)C(=O)O"),
    ScaffoldSeed("Cysteine", "Amino acid", "Proteinogenic amino acids", "N[C@@H](CS)C(=O)O"),
    ScaffoldSeed("Methionine", "Amino acid", "Proteinogenic amino acids", "CSCC[C@H](N)C(=O)O"),
    ScaffoldSeed("Phenylalanine", "Amino acid", "Proteinogenic amino acids", "N[C@@H](Cc1ccccc1)C(=O)O"),
    ScaffoldSeed("Tyrosine", "Amino acid", "Proteinogenic amino acids", "N[C@@H](Cc1ccc(O)cc1)C(=O)O"),
    ScaffoldSeed("Tryptophan", "Amino acid", "Proteinogenic amino acids", "N[C@@H](Cc1c[nH]c2ccccc12)C(=O)O"),
    ScaffoldSeed("Aspartic acid", "Amino acid", "Proteinogenic amino acids", "N[C@@H](CC(=O)O)C(=O)O"),
    ScaffoldSeed("Glutamic acid", "Amino acid", "Proteinogenic amino acids", "N[C@@H](CCC(=O)O)C(=O)O"),
    ScaffoldSeed("Asparagine", "Amino acid", "Proteinogenic amino acids", "N[C@@H](CC(N)=O)C(=O)O"),
    ScaffoldSeed("Glutamine", "Amino acid", "Proteinogenic amino acids", "N[C@@H](CCC(N)=O)C(=O)O"),
    ScaffoldSeed("Lysine", "Amino acid", "Proteinogenic amino acids", "NCCCC[C@H](N)C(=O)O"),
    ScaffoldSeed("Arginine", "Amino acid", "Proteinogenic amino acids", "N=C(N)NCCC[C@H](N)C(=O)O"),
    ScaffoldSeed("Histidine", "Amino acid", "Proteinogenic amino acids", "N[C@@H](Cc1c[nH]cn1)C(=O)O"),
    ScaffoldSeed("Proline", "Amino acid", "Proteinogenic amino acids", "OC(=O)[C@@H]1CCCN1"),
]

REQUESTED_SCAFFOLD_FAMILIES = [
    ScaffoldSeed("Ethylene glycol", "Polyether", "Glycol and glyme scaffolds", "OCCO"),
    ScaffoldSeed("Diethylene glycol", "Polyether", "Glycol and glyme scaffolds", "OCCOCCO"),
    ScaffoldSeed("Triethylene glycol", "Polyether", "Glycol and glyme scaffolds", "OCCOCCOCCO"),
    ScaffoldSeed("Polyethylene glycol repeat", "Polyether", "Glycol and glyme scaffolds", "COCCOC"),
    ScaffoldSeed("Monoglyme", "Polyether", "Glyme scaffolds", "COCCOC"),
    ScaffoldSeed("Diglyme", "Polyether", "Glyme scaffolds", "COCCOCCOC"),
    ScaffoldSeed("Triglyme", "Polyether", "Glyme scaffolds", "COCCOCCOCCOC"),
    ScaffoldSeed("Paclitaxel taxane core", "Taxane", "Taxol/paclitaxel scaffolds", "CC1=C2C(C(=O)C3(C)C(O)CC4OC4C3OC(=O)c3ccccc3)C(C)(O)C(O)C2OC1=O"),
    ScaffoldSeed("Taxane diterpene scaffold", "Taxane", "Taxol/paclitaxel scaffolds", "C1CC2CCC3C(C2)C13"),
    ScaffoldSeed("Gallic acid", "Tannin/polyphenol", "Hydrolyzable tannin scaffolds", "O=C(O)c1cc(O)c(O)c(O)c1"),
    ScaffoldSeed("Pyrogallol", "Tannin/polyphenol", "Tannin phenolic scaffolds", "Oc1cccc(O)c1O"),
    ScaffoldSeed("Catechol", "Tannin/polyphenol", "Condensed tannin scaffolds", "Oc1ccccc1O"),
    ScaffoldSeed("Ellagic acid", "Tannin/polyphenol", "Ellagitannin scaffolds", "O=c1oc2cc(O)c(O)cc2c2cc(O)c(O)cc12"),
    ScaffoldSeed("Gallotannin phenolic core", "Tannin/polyphenol", "Hydrolyzable tannin scaffolds", "O=C(Oc1cc(O)c(O)c(O)c1)c1cc(O)c(O)c(O)c1"),
]

SCAFFOLD_SEEDS = [*AMINO_ACID_SCAFFOLDS, *REQUESTED_SCAFFOLD_FAMILIES]
_SCHEMA_SEEDED_PATH: str | None = None

class ScaffoldRegistry:
    @staticmethod
    def ensure_schema_and_seed() -> None:
        global _SCHEMA_SEEDED_PATH
        db_path = str(get_db_path())
        if _SCHEMA_SEEDED_PATH == db_path:
            return
        with _get_connection_with_retry(read_only=False) as con:
            con.execute(GOLD_SCHEMA_SQL)
            existing = con.execute("SELECT COUNT(*) FROM scaffold_entries").fetchone()
        if existing and int(existing[0] or 0) >= len(SCAFFOLD_SEEDS):
            _SCHEMA_SEEDED_PATH = db_path
            return
        ScaffoldRegistry.upsert_seed_scaffolds()
        _SCHEMA_SEEDED_PATH = db_path

    @staticmethod
    def upsert_seed_scaffolds() -> int:
        rows = []
        now = _utc_now()
        for seed in SCAFFOLD_SEEDS:
            canonical, error = ChemistryEngine.canonicalize_smiles(seed.smiles)
            if error or canonical is None:
                raise RuntimeError(f"Seed scaffold {seed.name} has invalid SMILES: {error}")
            rows.append([seed.name, seed.category, seed.family, canonical, seed.source, seed.status, now, now])

        with _get_connection_with_retry(read_only=False) as con:
            con.executemany(
                """
                INSERT INTO scaffold_entries (
                    name, category, family, canonical_smiles, source, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    category = excluded.category,
                    family = excluded.family,
                    canonical_smiles = excluded.canonical_smiles,
                    source = excluded.source,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                rows,
            )
        return len(rows)

    @staticmethod
    def add_scaffold_by_smiles(name: str, category: str, family: str, smiles: str, source: str = "manual") -> dict[str, Any]:
        cleaned_name = name.strip()
        if not cleaned_name:
            return {"ok": False, "error": "Scaffold name is required."}

        canonical, error = ChemistryEngine.canonicalize_smiles(smiles)
        if error or canonical is None:
            return {"ok": False, "error": error or "Invalid SMILES."}

        cleaned_category = category.strip() or "Manual scaffold"
        cleaned_family = family.strip() or cleaned_category
        now = _utc_now()
        with _get_connection_with_retry(read_only=False) as con:
            con.execute(
                """
                INSERT INTO scaffold_entries (
                    name, category, family, canonical_smiles, source, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    category = excluded.category,
                    family = excluded.family,
                    canonical_smiles = excluded.canonical_smiles,
                    source = excluded.source,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                [cleaned_name, cleaned_category, cleaned_family, canonical, source, now, now],
            )
        return {
            "ok": True,
            "name": cleaned_name,
            "category": cleaned_category,
            "family": cleaned_family,
            "canonical_smiles": canonical,
            "source": source,
            "status": "active",
        }

    @staticmethod
    def list_scaffolds(limit: int = 1000, query: str = "") -> list[dict[str, Any]]:
        ScaffoldRegistry.ensure_schema_and_seed()
        params: list[Any] = []
        where_clause = "WHERE status = 'active'"
        if query.strip():
            term = f"%{query.strip().lower()}%"
            where_clause += """
                AND (
                    LOWER(name) LIKE ?
                    OR LOWER(category) LIKE ?
                    OR LOWER(family) LIKE ?
                    OR LOWER(canonical_smiles) LIKE ?
                )
            """
            params.extend([term, term, term, term])
        params.append(limit)
        with _get_connection_with_retry(read_only=True) as con:
            rows = con.execute(
                f"""
                SELECT name, category, family, canonical_smiles, source, status, created_at, updated_at
                FROM scaffold_entries
                {where_clause}
                ORDER BY category ASC, family ASC, name ASC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [
            {
                "name": row[0],
                "category": row[1],
                "family": row[2],
                "canonical_smiles": row[3],
                "source": row[4],
                "status": row[5],
                "created_at": row[6],
                "updated_at": row[7],
            }
            for row in rows
        ]
