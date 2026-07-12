from __future__ import annotations

from collections.abc import Callable, Sequence

from backend.simulation.model import ReactionNetwork


def build_rhs(network: ReactionNetwork) -> tuple[Callable[[float, Sequence[float]], list[float]], list[str]]:
    names = network.species_names()
    index = {name: i for i, name in enumerate(names)}

    # Precompute per-reaction (reactant terms, net stoichiometry) to keep the hot loop cheap.
    compiled = []
    for rxn in network.reactions:
        reactant_terms = [(index[sp], coeff) for sp, coeff in rxn.reactants.items()]
        net_delta: dict[int, int] = {}
        for sp, coeff in rxn.reactants.items():
            net_delta[index[sp]] = net_delta.get(index[sp], 0) - coeff
        for sp, coeff in rxn.products.items():
            net_delta[index[sp]] = net_delta.get(index[sp], 0) + coeff
        compiled.append((rxn.k, reactant_terms, list(net_delta.items())))

    n = len(names)

    def rhs(_t: float, y: Sequence[float]) -> list[float]:
        dydt = [0.0] * n
        for k, reactant_terms, net_delta in compiled:
            rate = k
            for idx, coeff in reactant_terms:
                conc = y[idx]
                rate *= conc ** coeff if coeff != 1 else conc
            if rate == 0.0:
                continue
            for idx, delta in net_delta:
                dydt[idx] += delta * rate
        return dydt

    return rhs, names
