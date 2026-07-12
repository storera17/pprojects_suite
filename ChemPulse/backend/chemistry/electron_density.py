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