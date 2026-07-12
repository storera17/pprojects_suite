from __future__ import annotations

import re
from dataclasses import dataclass, field


class NetworkError(ValueError):
    """A reaction network could not be parsed or is inconsistent."""


@dataclass
class Species:
    name: str
    initial: float = 0.0


@dataclass
class Reaction:
    reactants: dict[str, int]  # species name -> stoichiometric coefficient
    products: dict[str, int]
    k: float                   # rate constant (mass-action)
    label: str = ""


@dataclass
class ReactionNetwork:
    species: list[Species]
    reactions: list[Reaction]
    t_end: float = 10.0
    n_points: int = 200

    def species_names(self) -> list[str]:
        return [s.name for s in self.species]

    def validate(self) -> None:
        names = set(self.species_names())
        if not names:
            raise NetworkError("Add at least one species.")
        if not self.reactions:
            raise NetworkError("Add at least one reaction.")
        for rxn in self.reactions:
            for side in (rxn.reactants, rxn.products):
                for sp in side:
                    if sp not in names:
                        raise NetworkError(f"Reaction references unknown species '{sp}'.")
        if self.t_end <= 0:
            raise NetworkError("End time must be positive.")

    # --- construction from the UI / API payloads --------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> ReactionNetwork:
        species = [Species(str(s["name"]).strip(), float(s.get("initial", 0.0)))
                   for s in data.get("species", [])]
        reactions = []
        for r in data.get("reactions", []):
            reactions.append(Reaction(
                reactants={str(k): int(v) for k, v in dict(r.get("reactants", {})).items()},
                products={str(k): int(v) for k, v in dict(r.get("products", {})).items()},
                k=float(r.get("k", 0.0)),
                label=str(r.get("label", "")),
            ))
        net = cls(
            species=species,
            reactions=reactions,
            t_end=float(data.get("t_end", 10.0)),
            n_points=int(data.get("n_points", 200)),
        )
        net.validate()
        return net

    @classmethod
    def from_text(cls, species_text: str, reactions_text: str,
                  t_end: float = 10.0, n_points: int = 200) -> ReactionNetwork:
        """Parse the workbench's line-based editor.

        Species lines: ``A = 1.0`` (name = initial concentration).
        Reaction lines: ``2A + B -> C, k=0.5`` (``->`` separates the two sides;
        an optional integer prefix is the stoichiometric coefficient).
        """
        species: list[Species] = []
        for raw in species_text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise NetworkError(f"Species line needs 'name = value': '{line}'")
            name, value = line.split("=", 1)
            species.append(Species(name.strip(), _to_float(value, f"species '{name.strip()}'")))

        reactions: list[Reaction] = []
        for raw in reactions_text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            reactions.append(_parse_reaction(line))

        net = cls(species=species, reactions=reactions, t_end=t_end, n_points=n_points)
        net.validate()
        return net


_TOKEN = re.compile(r"^\s*(\d*)\s*([A-Za-z][A-Za-z0-9_]*)\s*$")


def _to_float(text: str, what: str) -> float:
    try:
        return float(text.strip())
    except ValueError as exc:
        raise NetworkError(f"Could not read a number for {what}: '{text.strip()}'") from exc


def _parse_side(side: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    side = side.strip()
    if not side or side == "0":
        return counts  # empty side (e.g. degradation to nothing)
    for term in side.split("+"):
        match = _TOKEN.match(term)
        if not match:
            raise NetworkError(f"Could not parse species term '{term.strip()}'")
        coeff = int(match.group(1)) if match.group(1) else 1
        name = match.group(2)
        counts[name] = counts.get(name, 0) + coeff
    return counts


def _parse_reaction(line: str) -> Reaction:
    label = ""
    body = line
    rate_text = ""
    # Split off ", k=..." (rate constant), tolerating an optional trailing label.
    if "," in body:
        body, rest = body.split(",", 1)
        for part in rest.split(","):
            part = part.strip()
            if part.lower().startswith("k"):
                rate_text = part.split("=", 1)[1] if "=" in part else ""
            elif part:
                label = part
    if "->" not in body:
        raise NetworkError(f"Reaction needs '->' between reactants and products: '{line}'")
    left, right = body.split("->", 1)
    if not rate_text:
        raise NetworkError(f"Reaction needs a rate constant 'k=...': '{line}'")
    return Reaction(
        reactants=_parse_side(left),
        products=_parse_side(right),
        k=_to_float(rate_text, "rate constant"),
        label=label,
    )
