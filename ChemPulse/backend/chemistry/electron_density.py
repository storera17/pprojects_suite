from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

# Aufbau filling order as (n, l, capacity). Enough to cover the whole periodic table in practice.
_AUFBAU: list[tuple[int, int, int]] = [
    (1, 0, 2),
    (2, 0, 2),
    (2, 1, 6),
    (3, 0, 2),
    (3, 1, 6),
    (4, 0, 2),
    (3, 2, 10),
    (4, 1, 6),
    (5, 0, 2),
    (4, 2, 10),
    (5, 1, 6),
    (6, 0, 2),
    (4, 3, 14),
    (5, 2, 10),
    (6, 1, 6),
    (7, 0, 2),
    (5, 3, 14),
    (6, 2, 10),
    (7, 1, 6),
]


# Effective principal quantum number n* per shell (Slater's tabulated values).
_N_STAR: dict[int, float] = {1: 1.0, 2: 2.0, 3: 3.0, 4: 3.7, 5: 4.0, 6: 4.2, 7: 4.3}

# Bohr Radius
_BOHR_TO_ANGSTROM = 0.529177

_EMBED_SEED = 0xF00D  # fixed so conformers (and therefore fields) are deterministic.MBED_SEED = 0xF00D  # fixed so conformers (and therefore fields) are deterministic.


@dataclass
class Orbital:
    n: int
    kind: str  # "sp", "d", or "f"
    occupancy: int
    zeff: float
    r_eff_angstrom: float

    @property
    def amplitude(self) -> float:
        n_star = _N_STAR.get(self.n, 4.3)
        return self.occupancy * self.zeff / n_star


@dataclass
class ElectronDensityField:
    origin: np.ndarray
    spacing: float
    values: np.ndarray  # normalized to [-1, 1]
    coords: np.ndarray
    symbols: list[str]

    def sample_at(self, points: np.ndarray) -> np.ndarray:
        """Nearest-grid-point field value at each (N, 3) world-space point."""
        idx = np.rint((points - self.origin) / self.spacing).astype(int)
        idx = np.clip(idx, 0, np.array(self.values.shape) - 1)
        return self.values[idx[:, 0], idx[:, 1], idx[:, 2]]
    
class ElectronDensitySurrogate:
    # -- atomic physics ---------------------------------------------------------

    @staticmethod
    def orbital_table(atomic_number: int) -> list[Orbital]:
        """Slater decomposition of a neutral atom into screened orbitals."""
        occupancies = _subshell_occupancies(atomic_number)
        groups = _slater_groups(occupancies)
        orbitals: list[Orbital] = []
        for (n, kind), occ in groups.items():
            if occ <= 0:
                continue
            screening = _slater_screening(groups, n, kind)
            zeff = max(atomic_number - screening, 0.1)
            n_star = _N_STAR.get(n, 4.3)
            r_eff_bohr = (n_star**2) / zeff
            orbitals.append(Orbital(n, kind, occ, round(zeff, 4), round(r_eff_bohr * _BOHR_TO_ANGSTROM, 4)))
        return orbitals

    @staticmethod
    def effective_nuclear_charge(atomic_number: int, n: int, kind: str) -> float:
        occupancies = _subshell_occupancies(atomic_number)
        groups = _slater_groups(occupancies)
        return round(atomic_number - _slater_screening(groups, n, kind), 4)

    # -- field ------------------------------------------------------------------

    @staticmethod
    def compute_field(
        smiles: str,
        *,
        spacing: float = 0.6,
        padding: float = 3.0,
        max_points_per_axis: int = 24,
    ) -> ElectronDensityField | None:
        """Embed a 3D conformer and build the normalized screened-charge field, or None.

        Memoized by (smiles, grid params): the field is deterministic (fixed embed seed), so
        the same molecule — which recurs constantly across closeness scoring, retrieval eval,
        and API detail requests — is computed once and reused read-only.
        """
        return _compute_field_cached(smiles, spacing, padding, max_points_per_axis)

    @staticmethod
    def _build_field(
        smiles: str, spacing: float, padding: float, max_points_per_axis: int
    ) -> ElectronDensityField | None:
        mol = _embed(smiles)
        if mol is None:
            return None

        conformer = mol.GetConformer()
        coords = np.array([list(conformer.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())], dtype=float)
        symbols = [atom.GetSymbol() for atom in mol.GetAtoms()]

        lower = coords.min(axis=0) - padding
        upper = coords.max(axis=0) + padding
        span = upper - lower
        # Coarsen spacing if the box would exceed the point cap on any axis.
        axis_points = np.ceil(span / spacing).astype(int) + 1
        if axis_points.max() > max_points_per_axis:
            spacing = float(span.max() / (max_points_per_axis - 1))
            axis_points = np.ceil(span / spacing).astype(int) + 1
        axis_points = np.clip(axis_points, 2, max_points_per_axis)

        gx = lower[0] + spacing * np.arange(axis_points[0])
        gy = lower[1] + spacing * np.arange(axis_points[1])
        gz = lower[2] + spacing * np.arange(axis_points[2])
        grid = np.stack(np.meshgrid(gx, gy, gz, indexing="ij"), axis=-1)  # (X, Y, Z, 3)
        flat = grid.reshape(-1, 3)

        field = np.zeros(flat.shape[0], dtype=float)
        for atom, center in zip(mol.GetAtoms(), coords, strict=True):
            orbitals = ElectronDensitySurrogate.orbital_table(atom.GetAtomicNum())
            if not orbitals:
                continue
            dist2 = np.sum((flat - center) ** 2, axis=1)
            for orbital in orbitals:
                r_eff = max(orbital.r_eff_angstrom, 1e-3)
                # Inverse-relationship falloff; tight orbitals (small r_eff) decay fastest.
                field += orbital.amplitude / (1.0 + dist2 / (r_eff**2))

        field = field.reshape(tuple(axis_points))
        return ElectronDensityField(
            origin=lower,
            spacing=spacing,
            values=_normalize_pm1(field),
            coords=coords,
            symbols=symbols,
        )

    # -- weak-portion (reactive-site) map --------------------------------------

    @staticmethod
    def weak_portions(
        field: ElectronDensityField,
        reacting_atom_indices: list[int] | None = None,
        *,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Rank atoms as candidate reactive sites from field extremity + local gradient.

        Local extrema and high-gradient regions of the field correspond to the most
        nucleophilic/electrophilic sites. Where a high-gradient atom coincides with an
        atom that the atom-mapping stage flagged as reacting, confidence is raised.
        """
        gradient = np.gradient(field.values, field.spacing)
        gradient_magnitude = np.sqrt(sum(component**2 for component in gradient))

        reacting = set(reacting_atom_indices or [])
        idx = np.rint((field.coords - field.origin) / field.spacing).astype(int)
        idx = np.clip(idx, 0, np.array(field.values.shape) - 1)

        atom_field = field.values[idx[:, 0], idx[:, 1], idx[:, 2]]
        atom_grad = gradient_magnitude[idx[:, 0], idx[:, 1], idx[:, 2]]
        grad_scale = float(atom_grad.max()) or 1.0

        sites: list[dict[str, Any]] = []
        for i, symbol in enumerate(field.symbols):
            extremity = abs(float(atom_field[i]))  # far from mid-field => stronger site
            grad_norm = float(atom_grad[i]) / grad_scale
            score = 0.6 * grad_norm + 0.4 * extremity
            confirmed = i in reacting
            sites.append(
                {
                    "atom_index": i,
                    "symbol": symbol,
                    "field_value": round(float(atom_field[i]), 4),
                    "gradient": round(float(atom_grad[i]), 4),
                    "reactive_score": round(min(1.0, score if not confirmed else 0.5 + 0.5 * score), 4),
                    "confirmed_by_atom_mapping": confirmed,
                }
            )
        sites.sort(key=lambda s: s["reactive_score"], reverse=True)
        return sites[:top_k]

    # -- predicted-vs-actual closeness -----------------------------------------

    @staticmethod
    def closeness_score(smiles_a: str, smiles_b: str) -> dict[str, Any]:
        """Composite structural closeness in [0, 1] for a predicted vs actual product.

        Blends an alignment-free electron-field-distribution similarity with a standard 2D
        Morgan-fingerprint Tanimoto and a molecular-formula match. The field term captures
        3D electron-distribution shape; the fingerprint captures 2D topology; the formula
        guards against right-shape/wrong-composition matches.
        """
        mol_a = Chem.MolFromSmiles(smiles_a)
        mol_b = Chem.MolFromSmiles(smiles_b)
        if mol_a is None or mol_b is None:
            return {"closeness_score": 0.0, "components": {}, "reason": "invalid_smiles"}

        fingerprint_similarity = _tanimoto(mol_a, mol_b)
        formula_match = 1.0 if rdMolDescriptors.CalcMolFormula(mol_a) == rdMolDescriptors.CalcMolFormula(mol_b) else 0.0

        field_a = ElectronDensitySurrogate.compute_field(smiles_a)
        field_b = ElectronDensitySurrogate.compute_field(smiles_b)
        if field_a is not None and field_b is not None:
            field_similarity = _field_distribution_similarity(field_a, field_b)
        else:
            field_similarity = fingerprint_similarity  # fall back if 3D embedding failed

        composite = 0.5 * field_similarity + 0.4 * fingerprint_similarity + 0.1 * formula_match
        return {
            "closeness_score": round(float(min(1.0, max(0.0, composite))), 4),
            "components": {
                "field_similarity": round(float(field_similarity), 4),
                "fingerprint_tanimoto": round(float(fingerprint_similarity), 4),
                "formula_match": formula_match,
            },
        }

    # -- validation against a cheap reference -----------------------------------

    @staticmethod
    def cross_validate_gasteiger(smiles: str) -> dict[str, Any]:
        """Check the surrogate against RDKit Gasteiger partial charges on the same molecule.

        Electron-rich regions (high field) should track electron-rich atoms (negative
        Gasteiger charge), so we expect an anti-correlation. Reports the correlation and a
        pass/flag verdict rather than trusting the surrogate blindly (design principle §6).
        """
        field = ElectronDensitySurrogate.compute_field(smiles)
        if field is None:
            return {"correlation": 0.0, "agrees": False, "reason": "embedding_failed", "n_atoms": 0}

        mol = _embed(smiles)
        AllChem.ComputeGasteigerCharges(mol)
        charges = np.array([float(atom.GetDoubleProp("_GasteigerCharge")) for atom in mol.GetAtoms()])
        charges = np.nan_to_num(charges, nan=0.0, posinf=0.0, neginf=0.0)
        atom_field = field.sample_at(field.coords)

        if np.std(charges) < 1e-9 or np.std(atom_field) < 1e-9 or len(charges) < 3:
            return {
                "correlation": 0.0,
                "agrees": False,
                "reason": "insufficient_variation",
                "n_atoms": int(len(charges)),
            }

        correlation = float(np.corrcoef(atom_field, charges)[0, 1])
        return {
            "correlation": round(correlation, 4),
            # High field should mean electron-rich => negative charge => negative correlation.
            "agrees": correlation <= -0.2,
            "n_atoms": int(len(charges)),
        }


# -- Slater's rules internals ---------------------------------------------------


def _subshell_occupancies(atomic_number: int) -> dict[tuple[int, int], int]:
    remaining = max(int(atomic_number), 0)
    occupancies: dict[tuple[int, int], int] = {}
    for n, azimuthal, capacity in _AUFBAU:
        if remaining <= 0:
            break
        fill = min(capacity, remaining)
        occupancies[(n, azimuthal)] = fill
        remaining -= fill
    return occupancies


def _group_key(n: int, azimuthal: int) -> tuple[int, str]:
    if azimuthal <= 1:
        return (n, "sp")
    if azimuthal == 2:
        return (n, "d")
    return (n, "f")


def _slater_groups(occupancies: dict[tuple[int, int], int]) -> dict[tuple[int, str], int]:
    groups: dict[tuple[int, str], int] = {}
    for (n, azimuthal), occ in occupancies.items():
        key = _group_key(n, azimuthal)
        groups[key] = groups.get(key, 0) + occ
    return groups


def _group_order(group: tuple[int, str]) -> tuple[int, int]:
    n, kind = group
    rank = {"sp": 0, "d": 1, "f": 2}[kind]
    return (n, rank)


def _slater_screening(groups: dict[tuple[int, str], int], n: int, kind: str) -> float:
    target = (n, kind)
    target_order = _group_order(target)
    screening = 0.0
    for group, occ in groups.items():
        if group == target:
            same_group_weight = 0.30 if group == (1, "sp") else 0.35
            screening += (occ - 1) * same_group_weight
            continue
        if _group_order(group) >= target_order:
            continue  # electrons in higher/equal groups do not screen
        group_n = group[0]
        if kind == "sp":
            if group_n == n - 1:
                screening += occ * 0.85
            elif group_n <= n - 2:
                screening += occ * 1.00
        else:  # d or f electrons: everything to the left screens fully
            screening += occ * 1.00
    return screening


# -- geometry / similarity internals -------------------------------------------


@lru_cache(maxsize=512)
def _compute_field_cached(
    smiles: str, spacing: float, padding: float, max_points_per_axis: int
) -> ElectronDensityField | None:
    return ElectronDensitySurrogate._build_field(smiles, spacing, padding, max_points_per_axis)


def _embed(smiles: str) -> Chem.Mol | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = _EMBED_SEED
    if AllChem.EmbedMolecule(mol, params) != 0:
        # Retry with random coordinates for awkward/small systems.
        params.useRandomCoords = True
        if AllChem.EmbedMolecule(mol, params) != 0:
            return None
    try:
        # A light cleanup is enough for a ranking surrogate; the field doesn't need a fully
        # minimized geometry, so cap iterations low to keep embedding cheap.
        AllChem.MMFFOptimizeMolecule(mol, maxIters=50)
    except Exception:
        pass
    return mol


def _normalize_pm1(field: np.ndarray) -> np.ndarray:
    low = float(field.min())
    high = float(field.max())
    if high - low < 1e-12:
        return np.zeros_like(field)
    return 2.0 * (field - low) / (high - low) - 1.0


def _field_distribution_similarity(a: ElectronDensityField, b: ElectronDensityField) -> float:
    """Alignment-free similarity: correlate the two fields' value histograms.

    Both fields are normalized to ``[-1, 1]``, so their value distributions are directly
    comparable without solving the 3D superposition problem. This is the deterministic
    surrogate for the design's "align fields then grid-correlate" step.
    """
    bins = np.linspace(-1.0, 1.0, 33)
    hist_a, _ = np.histogram(a.values.ravel(), bins=bins, density=True)
    hist_b, _ = np.histogram(b.values.ravel(), bins=bins, density=True)
    if np.std(hist_a) < 1e-12 or np.std(hist_b) < 1e-12:
        return 0.0
    correlation = float(np.corrcoef(hist_a, hist_b)[0, 1])
    return max(0.0, correlation)  # map [-1,1] correlation onto a [0,1] similarity


def _tanimoto(mol_a: Chem.Mol, mol_b: Chem.Mol) -> float:
    from rdkit import DataStructs

    from backend.chemistry.rdkit_engine import morgan_fingerprint

    fp_a = morgan_fingerprint(mol_a, 2, 2048)
    fp_b = morgan_fingerprint(mol_b, 2, 2048)
    return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))
