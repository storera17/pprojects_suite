from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import numpy as np

from backend.chemistry.electron_density import ElectronDensitySurrogate
from backend.data.reaction_repository import ReactionRepository
from backend.ml.anomaly import detect_anomalies
from backend.ml.features import FEATURE_NAMES, ReactionExample
from backend.ml.preprocessing import ReactionPreprocessor, clean_reactions
from backend.utils.paths import storage_dir

MODEL_ARTIFACT_NAME = "model.joblib"
_CLOSENESS_SAMPLE_CAP = 25


class ReactionTrainer:
    @staticmethod
    def train(
        reactions: list[dict[str, Any]] | None = None,
        *,
        run_id: str = "",
        test_size: float = 0.2,
        val_size: float = 0.2,
        random_state: int = 0,
    ) -> dict[str, Any]:
        """Train the scaffold classifier + retriever and persist a model run. Returns its summary."""
        source = reactions if reactions is not None else ReactionRepository.list_reactions(limit=100_000)
        examples, summary = clean_reactions(source)

        resolved_run_id = run_id or _run_id(examples)
        if len(examples) < 2 or len({e.scaffold_label for e in examples}) < 2:
            summary["notes"].append("insufficient data for a train/val/test split; not enough labeled classes")
            ReactionRepository.record_model_run(
                resolved_run_id,
                "none",
                "scaffold_classification",
                preprocessing_summary=summary,
                metrics={},
                status="insufficient_data",
            )
            return {
                "run_id": resolved_run_id,
                "status": "insufficient_data",
                "preprocessing_summary": summary,
                "metrics": {},
            }

        features = np.array([e.features for e in examples])
        labels = np.array([e.scaffold_label for e in examples])

        train_idx, val_idx, test_idx = _three_way_split(len(examples), labels, test_size, val_size, random_state)

        anomalies = detect_anomalies(examples, features)
        summary["anomalies"] = anomalies
        summary["notes"].append(f"{anomalies['flagged_count']} rows flagged by anomaly detection (kept for review)")

        # Fit the preprocessing pipeline on the TRAIN split only, then apply it everywhere.
        preprocessor = ReactionPreprocessor().fit(features[train_idx])
        summary["imputed_numeric_columns"] = preprocessor.imputed_columns
        x_train = preprocessor.transform(features[train_idx])
        x_val = preprocessor.transform(features[val_idx]) if len(val_idx) else x_train[:0]
        x_test = preprocessor.transform(features[test_idx]) if len(test_idx) else x_train
        y_train, y_val, y_test = labels[train_idx], labels[val_idx], labels[test_idx if len(test_idx) else train_idx]

        candidates = _candidate_models(random_state)
        comparison: dict[str, float] = {}
        fitted: dict[str, Any] = {}
        for name, model in candidates.items():
            model.fit(x_train, y_train)
            fitted[name] = model
            eval_x, eval_y = (x_val, y_val) if len(val_idx) else (x_train, y_train)
            comparison[name] = _balanced_accuracy(eval_y, model.predict(eval_x))

        best_name = max(comparison, key=comparison.get)
        best_model = fitted[best_name]

        metrics = _classification_metrics(best_model, x_test, y_test)
        metrics["model_comparison_balanced_accuracy"] = {k: round(v, 4) for k, v in comparison.items()}

        retriever = _ProductRetriever.fit([examples[i] for i in train_idx], x_train)
        metrics["retrieval"] = retriever.evaluate([examples[i] for i in test_idx], x_test)
        metrics["electron_density_closeness"] = _closeness_distribution(
            retriever, [examples[i] for i in test_idx], x_test
        )

        artifact_path = _persist_artifact(resolved_run_id, preprocessor, best_model, best_name, retriever)

        split = {
            "train": len(train_idx),
            "val": len(val_idx),
            "test": len(test_idx),
            "classes": sorted({str(c) for c in labels}),
        }
        ReactionRepository.record_model_run(
            resolved_run_id,
            best_name,
            "scaffold_classification",
            dataset_hash=_dataset_hash(examples),
            split=split,
            preprocessing_summary=summary,
            metrics=metrics,
            artifact_path=artifact_path,
            status="completed",
        )
        return {
            "run_id": resolved_run_id,
            "status": "completed",
            "model_name": best_name,
            "artifact_path": artifact_path,
            "split": split,
            "preprocessing_summary": summary,
            "metrics": metrics,
        }


class _ProductRetriever:
    """Fingerprint nearest-neighbor retrieval: nearest known reaction's product."""

    def __init__(self, nn: Any, products: list[str], inchikeys: list[str]) -> None:
        self._nn = nn
        self._products = products
        self._inchikeys = inchikeys

    @classmethod
    def fit(cls, examples: list[ReactionExample], x_train: np.ndarray) -> _ProductRetriever:
        from sklearn.neighbors import NearestNeighbors

        neighbors = min(5, max(1, len(examples)))
        nn = NearestNeighbors(n_neighbors=neighbors).fit(x_train)
        return cls(nn, [e.product_smiles for e in examples], [e.product_inchikey for e in examples])

    def query(self, x_row: np.ndarray, top_k: int = 5) -> list[str]:
        k = min(top_k, len(self._products))
        if k == 0:
            return []
        _, indices = self._nn.kneighbors(x_row.reshape(1, -1), n_neighbors=k)
        return [self._products[i] for i in indices[0]]

    def evaluate(self, examples: list[ReactionExample], x_test: np.ndarray, top_k: int = 5) -> dict[str, Any]:
        if not len(examples):
            return {"top_1_accuracy": None, "top_k_accuracy": None, "k": top_k, "n": 0}
        hits_1 = 0
        hits_k = 0
        for example, row in zip(examples, x_test, strict=True):
            retrieved = self.query(row, top_k=top_k)
            retrieved_keys = [_inchikey(s) for s in retrieved]
            if retrieved_keys and retrieved_keys[0] == example.product_inchikey:
                hits_1 += 1
            if example.product_inchikey in retrieved_keys:
                hits_k += 1
        n = len(examples)
        return {
            "top_1_accuracy": round(hits_1 / n, 4),
            "top_k_accuracy": round(hits_k / n, 4),
            "k": top_k,
            "n": n,
        }


# -- metrics --------------------------------------------------------------------


def _classification_metrics(model: Any, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        confusion_matrix,
        f1_score,
    )

    predictions = model.predict(x)
    labels = sorted(set(y.tolist()) | set(predictions.tolist()))
    metrics: dict[str, Any] = {
        "accuracy": round(float(accuracy_score(y, predictions)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y, predictions)), 4),
        "macro_f1": round(float(f1_score(y, predictions, average="macro", zero_division=0)), 4),
        "micro_f1": round(float(f1_score(y, predictions, average="micro", zero_division=0)), 4),
        "labels": labels,
        "confusion_matrix": confusion_matrix(y, predictions, labels=labels).tolist(),
        "n_test": int(len(y)),
    }
    metrics["roc_auc_ovr"] = _safe_roc_auc(model, x, y)
    return metrics


def _safe_roc_auc(model: Any, x: np.ndarray, y: np.ndarray) -> float | None:
    if not hasattr(model, "predict_proba") or len(set(y.tolist())) < 2:
        return None
    try:
        from sklearn.metrics import roc_auc_score
        from sklearn.preprocessing import label_binarize

        classes = sorted(set(model.classes_.tolist()))
        y_bin = label_binarize(y, classes=classes)
        proba = model.predict_proba(x)
        if y_bin.shape[1] != proba.shape[1]:
            return None
        return round(float(roc_auc_score(y_bin, proba, average="macro", multi_class="ovr")), 4)
    except Exception:
        return None


def _closeness_distribution(
    retriever: _ProductRetriever, examples: list[ReactionExample], x_test: np.ndarray
) -> dict[str, Any]:
    """Electron-density closeness of retrieved vs actual product across the test set."""
    scores: list[float] = []
    for example, row in zip(examples[:_CLOSENESS_SAMPLE_CAP], x_test[:_CLOSENESS_SAMPLE_CAP], strict=False):
        retrieved = retriever.query(row, top_k=1)
        if not retrieved or not example.product_smiles:
            continue
        try:
            result = ElectronDensitySurrogate.closeness_score(retrieved[0], example.product_smiles)
            scores.append(result["closeness_score"])
        except Exception:
            continue
    if not scores:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None}
    arr = np.array(scores)
    return {
        "n": len(scores),
        "mean": round(float(arr.mean()), 4),
        "median": round(float(np.median(arr)), 4),
        "min": round(float(arr.min()), 4),
        "max": round(float(arr.max()), 4),
    }


# -- helpers --------------------------------------------------------------------


def _candidate_models(random_state: int) -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.svm import SVC

    return {
        "random_forest": RandomForestClassifier(n_estimators=200, random_state=random_state),
        "gradient_boosting": GradientBoostingClassifier(random_state=random_state),
        # No probability=True (deprecated in sklearn 1.9): confidence falls back to the SVM
        # margin via decision_function, and ROC-AUC is simply reported as None for the SVM.
        "svm": SVC(random_state=random_state),
    }


def _three_way_split(
    n: int, labels: np.ndarray, test_size: float, val_size: float, random_state: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stratified train/val/test indices, degrading to train-only when data is too thin."""
    indices = np.arange(n)
    from collections import Counter

    counts = Counter(labels.tolist())
    stratifiable = n >= 6 and min(counts.values()) >= 2 and len(counts) >= 2
    if not stratifiable:
        return indices, np.array([], dtype=int), np.array([], dtype=int)

    from sklearn.model_selection import train_test_split

    train_val, test = train_test_split(indices, test_size=test_size, random_state=random_state, stratify=labels)
    val_fraction = val_size / (1.0 - test_size)
    train_labels = labels[train_val]
    if len(train_val) < 4 or min(Counter(train_labels.tolist()).values()) < 2:
        return train_val, np.array([], dtype=int), test
    train, val = train_test_split(train_val, test_size=val_fraction, random_state=random_state, stratify=train_labels)
    return train, val, test


def _balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    from sklearn.metrics import balanced_accuracy_score

    return float(balanced_accuracy_score(y_true, y_pred))


def _persist_artifact(
    run_id: str,
    preprocessor: ReactionPreprocessor,
    model: Any,
    model_name: str,
    retriever: _ProductRetriever,
) -> str:
    import joblib

    directory = storage_dir() / "models" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / MODEL_ARTIFACT_NAME
    joblib.dump(
        {
            "pipeline": preprocessor._pipeline,
            "imputed_columns": preprocessor.imputed_columns,
            "model": model,
            "model_name": model_name,
            "classes": [str(c) for c in getattr(model, "classes_", [])],
            "feature_names": FEATURE_NAMES,
            "retriever_nn": retriever._nn,
            "retriever_products": retriever._products,
            "retriever_inchikeys": retriever._inchikeys,
        },
        path,
    )
    return str(path)


@lru_cache(maxsize=8192)
def _inchikey(smiles: str) -> str:
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles)
    return Chem.MolToInchiKey(mol) if mol else ""


def _dataset_hash(examples: list[ReactionExample]) -> str:
    payload = json.dumps(sorted(e.reaction_id + "|" + e.scaffold_label for e in examples))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _run_id(examples: list[ReactionExample]) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"run_{stamp}_{_dataset_hash(examples)[:8]}"
