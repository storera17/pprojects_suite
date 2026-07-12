from __future__ import annotations

SKLEARN_AVAILABLE: bool
try:  # pragma: no cover - trivial import guard
    import sklearn  # noqa: F401

    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover
    SKLEARN_AVAILABLE = False
