from __future__ import annotations

import logging
from typing import Any, Optional

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold