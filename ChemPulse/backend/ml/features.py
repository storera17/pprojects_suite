from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

from backend.chemistry.rdkit_engine import morgan_fingerprint

FINGERPRINT_BITS = 512

_DESCRIPTOR_NAMES = [
    "total_mw",
    "mean_logp",
    "total_hbd",
    "total_hba",
    "total_tpsa",
    "total_rings",
    "n_reactants",
]

FEATURE_NAMES: list[str] = [f"fp_{i}" for i in range(FINGERPRINT_BITS)] + _DESCRIPTOR_NAMES
FEATURE_DIM = len(FEATURE_NAMES)


@dataclass
class ReactionExample:
    reaction_id: str
    features: np.ndarray
    scaffold_label: str
    product_smiles: str
    product_inchikey: str
    yield_pct: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def reactant_features(reactant_smiles: list[str]) -> np.ndarray | None:
    """Aggregate a reactant set into one feature vector, or None if nothing parses."""
    mols = [m for m in (Chem.MolFromSmiles(s) for s in reactant_smiles) if m is not None]
    if not mols:
        return None

    bits = np.zeros(FINGERPRINT_BITS, dtype=float)
    for mol in mols:
        fingerprint = morgan_fingerprint(mol, 2, FINGERPRINT_BITS)
        bits = np.maximum(bits, np.array(fingerprint, dtype=float))  # bag-of-reactants (bitwise OR)

    descriptors = np.array(
        [
            sum(Descriptors.MolWt(m) for m in mols),
            float(np.mean([Descriptors.MolLogP(m) for m in mols])),
            sum(Descriptors.NumHDonors(m) for m in mols),
            sum(Descriptors.NumHAcceptors(m) for m in mols),
            sum(Descriptors.TPSA(m) for m in mols),
            sum(Descriptors.RingCount(m) for m in mols),
            float(len(mols)),
        ],
        dtype=float,
    )
    return np.concatenate([bits, descriptors])


def product_scaffold_label(product_smiles: list[str]) -> tuple[str, str, str]:
    """Return (scaffold_class, canonical_product_smiles, product_inchikey) for the first product."""
    for smiles in product_smiles:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
        scaffold = Chem.MolToSmiles(scaffold_mol) if scaffold_mol and scaffold_mol.GetNumAtoms() else ""
        return (scaffold or "acyclic", Chem.MolToSmiles(mol), Chem.MolToInchiKey(mol))
    return ("acyclic", "", "")


def build_examples(reactions: list[dict[str, Any]]) -> list[ReactionExample]:
    """Featurize reactions into training examples, skipping those that cannot be featurized."""
    examples: list[ReactionExample] = []
    for reaction in reactions:
        features = reactant_features(list(reaction.get("reactants") or []))
        if features is None:
            continue
        scaffold, product_smiles, product_inchikey = product_scaffold_label(list(reaction.get("products") or []))
        if not product_smiles:
            continue
        examples.append(
            ReactionExample(
                reaction_id=str(reaction.get("reaction_id") or reaction.get("id") or ""),
                features=features,
                scaffold_label=scaffold,
                product_smiles=product_smiles,
                product_inchikey=product_inchikey,
                yield_pct=_as_float(reaction.get("yield_pct")),
            )
        )
    return examples


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None and value != "" else None
    except (TypeError, ValueError):
        return None
