from __future__ import annotations

from typing import Any

import numpy as np

from backend.ml.features import ReactionExample


def detect_anomalies(
    examples: list[ReactionExample],
    features: np.ndarray,
    *,
    method: str = "isolation_forest",
    contamination: float = 0.1,
) -> dict[str, Any]:
    """Return anomaly flags: rule-based (impossible yields) + model-based (off-manifold)."""
    flags: list[dict[str, Any]] = []

    # Rule-based: yields that are physically impossible are unambiguous anomalies.
    for i, example in enumerate(examples):
        if example.yield_pct is not None and (example.yield_pct < 0 or example.yield_pct > 100):
            flags.append(
                {"row": i, "reaction_id": example.reaction_id, "reason": f"impossible_yield:{example.yield_pct}"}
            )

    model_flagged: list[int] = []
    if len(features) >= 4:  # detectors need a few points to be meaningful
        try:
            model_flagged = _model_outliers(features, method=method, contamination=contamination)
        except Exception as exc:  # pragma: no cover - defensive
            flags.append({"row": -1, "reason": f"detector_error:{exc.__class__.__name__}"})
    already = {f["row"] for f in flags}
    for i in model_flagged:
        if i not in already:
            flags.append({"row": i, "reaction_id": examples[i].reaction_id, "reason": "off_manifold"})

    return {
        "method": method,
        "flagged_count": len(flags),
        "flagged": flags,
    }


def _model_outliers(features: np.ndarray, *, method: str, contamination: float) -> list[int]:
    if method == "local_outlier_factor":
        from sklearn.neighbors import LocalOutlierFactor

        detector = LocalOutlierFactor(n_neighbors=min(20, len(features) - 1), contamination=contamination)
        predictions = detector.fit_predict(features)
    else:
        from sklearn.ensemble import IsolationForest

        detector = IsolationForest(contamination=contamination, random_state=0)
        predictions = detector.fit_predict(features)
    return [i for i, label in enumerate(predictions) if label == -1]
