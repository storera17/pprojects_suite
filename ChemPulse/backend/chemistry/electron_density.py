from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors