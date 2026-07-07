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
