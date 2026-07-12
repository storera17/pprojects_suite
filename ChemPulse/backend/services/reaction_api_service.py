from __future__ import annotations

from typing import Any

from backend.data.reaction_repository import ReactionRepository


class ReactionApiService:
    @staticmethod
    def list_reactions(limit: int = 200) -> dict[str, Any]:
        items = ReactionRepository.list_reactions_summary(limit=limit)
        return {"items": items, "metadata": {"record_count": len(items), "source": "silver_reactions"}}

    @staticmethod
    def reaction_detail(reaction_id: str) -> dict[str, Any] | None:
        """Full reaction record + electron-density overlay, or None if the id is unknown."""
        reaction = ReactionRepository.get_reaction(reaction_id)
        if reaction is None:
            return None
        reaction["electron_density"] = ReactionApiService._electron_density_overlay(
            reaction.get("products", []),
            reaction.get("reacting_atoms") or [],
        )
        return reaction

    @staticmethod
    def _electron_density_overlay(products: list[str], reacting_atoms: list[int]) -> dict[str, Any]:
        target = next((s for s in products if s), "")
        if not target:
            return {"available": False, "reason": "no_product_structure"}
        try:
            from backend.chemistry.electron_density import ElectronDensitySurrogate

            field = ElectronDensitySurrogate.compute_field(target)
            if field is None:
                return {"available": False, "reason": "embedding_failed", "product": target}
            weak = ElectronDensitySurrogate.weak_portions(field, reacting_atoms or None, top_k=5)
            return {
                "available": True,
                "product": target,
                "grid_shape": list(field.values.shape),
                "field_range": [round(float(field.values.min()), 4), round(float(field.values.max()), 4)],
                "weak_portions": weak,
            }
        except Exception as exc:  # pragma: no cover - defensive
            return {"available": False, "reason": f"error:{exc.__class__.__name__}"}
