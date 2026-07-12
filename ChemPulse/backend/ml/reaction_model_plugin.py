from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.plugins.base import PredictivePlugin

_ARTIFACT_CACHE: dict[str, Any] = {}


class ReactionModelPlugin(PredictivePlugin):
    plugin_name = "reaction_scaffold_model"
    plugin_version = "0.1.0"

    def supports(self, payload: dict[str, Any]) -> bool:
        # Only the reaction-prediction entry point (a reactant set); never the heuristic payloads.
        reactants = payload.get("reactants")
        return isinstance(reactants, list) and bool(reactants)

    def predict(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        bundle = _load_latest_artifact()
        if bundle is None:
            return []

        try:
            from backend.ml.features import reactant_features
        except Exception:  # pragma: no cover - defensive
            return []

        features = reactant_features([str(s) for s in payload["reactants"]])
        if features is None:
            return []

        transformed = bundle["pipeline"].transform(features.reshape(1, -1))
        model = bundle["model"]
        predicted = str(model.predict(transformed)[0])
        confidence = _confidence(model, transformed)
        products = _retrieve_products(bundle, transformed, top_k=int(payload.get("top_k", 3)))

        return [
            {
                "title": f"Predicted product scaffold: {predicted}",
                "reason": (
                    "Trained classical model (scaffold classification over Morgan fingerprints + RDKit "
                    "descriptors of the reactant set) with fingerprint nearest-neighbor product retrieval."
                ),
                "confidence": f"{round(confidence * 100)}%",
                "predicted_scaffold": predicted,
                "suggested_products": products,
                "model_name": bundle.get("model_name", "reaction_model"),
                "mechanism": "Classical ML scaffold classification + kNN product retrieval",
                "plugin": self.plugin_name,
                "limitation": (
                    "Literature-mined corpus is small; treat as decision support and confirm with the "
                    "electron-density closeness score and experimental characterization."
                ),
            }
        ]


def _load_latest_artifact() -> dict[str, Any] | None:
    try:
        import joblib  # noqa: F401

        from backend.data.reaction_repository import ReactionRepository
    except Exception:
        return None

    for run in ReactionRepository.list_model_runs(limit=50):
        artifact_path = run.get("artifact_path")
        if run.get("status") != "completed" or not artifact_path or not Path(artifact_path).exists():
            continue
        if artifact_path in _ARTIFACT_CACHE:
            return _ARTIFACT_CACHE[artifact_path]
        try:
            import joblib

            bundle = joblib.load(artifact_path)
        except Exception:
            continue
        _ARTIFACT_CACHE[artifact_path] = bundle
        return bundle
    return None


def _confidence(model: Any, transformed: Any) -> float:
    import numpy as np

    if hasattr(model, "predict_proba"):
        try:
            return float(max(model.predict_proba(transformed)[0]))
        except Exception:
            pass
    if hasattr(model, "decision_function"):
        try:
            scores = np.asarray(model.decision_function(transformed))
            if scores.ndim == 1:  # binary: a single signed margin
                return float(1.0 / (1.0 + np.exp(-abs(float(scores[0])))))
            row = scores[0]
            softmax = np.exp(row - row.max())
            return float((softmax / softmax.sum()).max())
        except Exception:
            pass
    return 0.0


def _retrieve_products(bundle: dict[str, Any], transformed: Any, top_k: int) -> list[str]:
    nn = bundle.get("retriever_nn")
    products = bundle.get("retriever_products") or []
    if nn is None or not products:
        return []
    k = min(top_k, len(products))
    try:
        _, indices = nn.kneighbors(transformed, n_neighbors=k)
    except Exception:
        return []
    seen: list[str] = []
    for i in indices[0]:
        product = products[i]
        if product and product not in seen:
            seen.append(product)
    return seen


def clear_artifact_cache() -> None:
    """Drop cached model bundles (used by tests after training a fresh model)."""
    _ARTIFACT_CACHE.clear()
