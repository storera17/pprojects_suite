from __future__ import annotations

import logging
from typing import Any, Optional

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

logger = logging.getLogger(__name__)

_MORGAN_GENERATORS: dict[tuple[int, int], Any] = {}


def morgan_generator(radius: int = 2, n_bits: int = 2048):
    key = (radius, n_bits)
    generator = _MORGAN_GENERATORS.get(key)
    if generator is None:
        generator = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
        _MORGAN_GENERATORS[key] = generator
    return generator


def morgan_fingerprint(mol: Chem.Mol, radius: int = 2, n_bits: int = 2048):
    return morgan_generator(radius, n_bits).GetFingerprint(mol)


class ChemistryEngine:
    @staticmethod
    def process_smiles(smiles: str) -> Optional[dict[str, Any]]:
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None

            Chem.SanitizeMol(mol)
            canonical_smiles = Chem.MolToSmiles(mol, canonical=True)

            scaffold_mol = MurckoScaffold.GetScaffoldForMol(mol)
            scaffold_smiles = Chem.MolToSmiles(scaffold_mol, canonical=True) if scaffold_mol else ""

            return {
                "smiles": canonical_smiles,
                "inchi_key": Chem.MolToInchiKey(mol),
                "scaffold": scaffold_smiles or "Acyclic",
                "mw": round(Descriptors.MolWt(mol), 2),
                "logp": round(Descriptors.MolLogP(mol), 2),
                "hbd": int(Descriptors.NumHDonors(mol)),
                "hba": int(Descriptors.NumHAcceptors(mol)),
                "tpsa": round(Descriptors.TPSA(mol), 2),
                "fingerprint": AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048).ToBitString(),
            }
        except Exception:
            logger.debug("Failed to process SMILES %r", smiles, exc_info=True)
            return None

    @staticmethod
    def canonicalize_smiles(smiles: str) -> tuple[str | None, str | None]:
        cleaned = smiles.strip()
        if not cleaned:
            return None, "SMILES is required."

        result = ChemistryEngine.process_smiles(cleaned)
        if result is None:
            return None, "Invalid SMILES. Check valence, ring closures, and atom syntax."
        return str(result["smiles"]), None