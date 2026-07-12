from __future__ import annotations

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from backend.simulation.model import ReactionNetwork
from backend.simulation.ode_builder import build_rhs


def simulate(network: ReactionNetwork) -> dict[str, Any]:
    """Integrate the network and return time-series concentrations per species."""
    network.validate()
    rhs, names = build_rhs(network)
    y0 = [s.initial for s in network.species]
    t_eval = np.linspace(0.0, network.t_end, max(2, network.n_points))

    solution = solve_ivp(
        rhs,
        (0.0, network.t_end),
        y0,
        t_eval=t_eval,
        method="LSODA",
        rtol=1e-6,
        atol=1e-9,
    )

    series = {names[i]: solution.y[i].tolist() for i in range(len(names))}
    return {
        "t": solution.t.tolist(),
        "species": names,
        "series": series,
        "success": bool(solution.success),
        "message": str(solution.message),
        "conserved_total": _total_mass_trace(series, solution.t.size),
    }


def _total_mass_trace(series: dict[str, list[float]], n: int) -> list[float]:
    """Sum of all species at each time point — flat only if every reaction conserves
    total moles; surfaced so the UI can show whether mass is (approximately) conserved."""
    totals = [0.0] * n
    for values in series.values():
        for i, v in enumerate(values):
            totals[i] += v
    return totals
