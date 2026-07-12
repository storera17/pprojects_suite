
from __future__ import annotations

from typing import Any

import numpy as np

from backend.ml.features import ReactionExample, build_examples


class ReactionPreprocessor:
    """Wraps a fitted sklearn Pipeline; refuses to transform before it is fit."""

    def __init__(self) -> None:
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        self._pipeline = Pipeline(
            steps=[
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]
        )
        self._fitted = False
        self.imputed_columns: int = 0

    def fit(self, x_train: np.ndarray) -> ReactionPreprocessor:
        self._pipeline.fit(x_train)
        self._fitted = True
        # Count columns that had at least one missing value the imputer had to fill.
        imputer = self._pipeline.named_steps["impute"]
        stats = getattr(imputer, "statistics_", None)
        self.imputed_columns = int(np.isnan(x_train).any(axis=0).sum()) if stats is not None else 0
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("ReactionPreprocessor.transform called before fit — this would leak or crash.")
        return self._pipeline.transform(x)

    def save(self, path: str) -> str:
        import joblib

        joblib.dump({"pipeline": self._pipeline, "imputed_columns": self.imputed_columns}, path)
        return path

    @classmethod
    def load(cls, path: str) -> ReactionPreprocessor:
        import joblib

        payload = joblib.load(path)
        instance = cls.__new__(cls)
        instance._pipeline = payload["pipeline"]
        instance._fitted = True
        instance.imputed_columns = int(payload.get("imputed_columns", 0))
        return instance


def clean_reactions(reactions: list[dict[str, Any]]) -> tuple[list[ReactionExample], dict[str, Any]]:
    """Featurize + clean reactions and return (examples, summary).

    Cleaning: featurization drops rows with unparseable structures; remaining rows are
    deduplicated by product InChIKey. Both counts feed the human-readable summary.
    """
    raw_count = len(reactions)
    examples = build_examples(reactions)
    featurized_count = len(examples)
    dropped_invalid = raw_count - featurized_count

    seen: set[str] = set()
    deduped: list[ReactionExample] = []
    for example in examples:
        key = example.product_inchikey or example.reaction_id or example.product_smiles
        if key in seen:
            continue
        seen.add(key)
        deduped.append(example)
    dedup_removed = featurized_count - len(deduped)

    summary = {
        "input_rows": raw_count,
        "dropped_invalid_smiles": dropped_invalid,
        "deduplicated_by_inchikey": dedup_removed,
        "retained_rows": len(deduped),
        "notes": [
            f"{raw_count} reaction rows received",
            f"{dropped_invalid} rows dropped for unparseable structures",
            f"{dedup_removed} rows deduplicated by product InChIKey",
            f"{len(deduped)} rows retained for modeling",
        ],
    }
    return deduped, summary
