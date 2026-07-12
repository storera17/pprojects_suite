from __future__ import annotations

from typing import Any

from backend.data.reaction_repository import ReactionRepository


class ModelMetricsService:
    @staticmethod
    def runs(limit: int = 50) -> list[dict[str, Any]]:
        return ReactionRepository.list_model_runs(limit=limit)

    @staticmethod
    def latest_completed_run() -> dict[str, Any] | None:
        for run in ReactionRepository.list_model_runs(limit=50):
            if run.get("status") == "completed":
                return run
        return None

    @staticmethod
    def dashboard() -> dict[str, Any]:
        """Dashboard payload: preprocessing summary first, then metrics, then run history."""
        runs = ModelMetricsService.runs()
        latest = ModelMetricsService.latest_completed_run()
        return {
            # Order matters for the UI: the summary is rendered above the metrics.
            "preprocessing_summary": (latest or {}).get("preprocessing_summary", {}),
            "metrics": (latest or {}).get("metrics", {}),
            "latest_run": latest,
            "runs": runs,
            "metadata": {
                "record_count": len(runs),
                "source": "gold_model_runs",
                "has_completed_run": latest is not None,
            },
        }

    @staticmethod
    def control_plane_payload(reaction_limit: int = 50) -> dict[str, Any]:
        """Graph nodes + metric records for Command Center's generic ingestion API.

        Reaction nodes and model-run nodes are emitted in a generic ``{nodes, metrics}`` shape
        so Command Center's ``control_plane_mapper`` can render them without ChemPulse-specific
        code. Metrics are flattened to scalar name/value pairs for the metrics panel.
        """
        reactions = ReactionRepository.list_reactions_summary(limit=reaction_limit)
        runs = ModelMetricsService.runs()

        nodes: list[dict[str, Any]] = []
        for reaction in reactions:
            nodes.append(
                {
                    "id": reaction["reaction_id"],
                    "type": "reaction",
                    "label": reaction.get("reaction_smiles") or reaction["reaction_id"],
                    "data": {
                        "products": reaction.get("products", []),
                        "yield_pct": reaction.get("yield_pct"),
                        "corroboration_count": reaction.get("corroboration_count"),
                        "credibility_score": reaction.get("credibility_score"),
                        "mechanism_source": reaction.get("mechanism_source"),
                    },
                }
            )
        for run in runs:
            nodes.append(
                {
                    "id": run["run_id"],
                    "type": "model_run",
                    "label": f"{run.get('model_name', 'model')} · {run.get('task', '')}",
                    "data": {"status": run.get("status"), "metrics": run.get("metrics", {})},
                }
            )

        metrics: list[dict[str, Any]] = []
        latest = ModelMetricsService.latest_completed_run()
        if latest:
            for name, value in _flatten_scalars(latest.get("metrics", {})):
                metrics.append({"run_id": latest["run_id"], "name": name, "value": value})

        return {
            "source": "chempulse",
            "kind": "reaction_intelligence",
            "nodes": nodes,
            "metrics": metrics,
        }

    @staticmethod
    def publish_to_command_center(base_url: str, *, timeout: float = 10.0) -> dict[str, Any]:
        """POST the control-plane payload to Command Center. Network-guarded."""
        payload = ModelMetricsService.control_plane_payload()
        try:
            import requests

            response = requests.post(
                f"{base_url.rstrip('/')}/api/control-plane/ingest",
                json=payload,
                timeout=timeout,
            )
            return {"ok": response.ok, "status_code": response.status_code, "nodes": len(payload["nodes"])}
        except Exception as exc:
            return {"ok": False, "error": exc.__class__.__name__, "nodes": len(payload["nodes"])}


def _flatten_scalars(obj: Any, prefix: str = "") -> list[tuple[str, float]]:
    """Flatten nested metric dicts into (dotted_name, numeric_value) pairs for the metrics panel."""
    pairs: list[tuple[str, float]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            pairs.extend(_flatten_scalars(value, f"{prefix}{key}."))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        pairs.append((prefix.rstrip("."), float(obj)))
    return pairs
