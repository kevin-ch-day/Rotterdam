"""K-nearest neighbour classifier for risk prediction.

This lightweight model demonstrates a simple machine learning component
for classifying apps as benign or malicious based on derived metrics.
The training data lives alongside this module in ``ml_baseline.json`` and
contains a handful of labelled examples.  During prediction we measure the
Euclidean distance between the input metrics and each training sample,
select the *k* closest neighbours and return the majority label along with
basic confidence information.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

_BASELINE_PATH = Path(__file__).with_name("ml_baseline.json")
_LOG = logging.getLogger(__name__)


def _load_baseline() -> List[Tuple[Dict[str, float], str]]:
    """Return training samples loaded from ``ml_baseline.json``.

    Any failure to load or parse the baseline is logged and results in an
    empty training set so callers can decide how to handle the absence of
    model data.
    """

    try:
        data = json.loads(_BASELINE_PATH.read_text())
    except FileNotFoundError:
        _LOG.warning("ML baseline not found: %s", _BASELINE_PATH)
        return []
    except json.JSONDecodeError as e:  # pragma: no cover - invalid baseline
        _LOG.warning("Invalid ML baseline JSON: %s", e)
        return []

    return [(entry["metrics"], entry["label"]) for entry in data]


_BASELINE = _load_baseline()


def _distance(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = set(a) | set(b)
    return sum((a.get(k, 0.0) - b.get(k, 0.0)) ** 2 for k in keys) ** 0.5


def _validate_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """Ensure all metric values are numeric within [0, 1]."""
    clean: Dict[str, float] = {}
    for name, value in metrics.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"Metric {name}={value!r} must be numeric")
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Metric {name}={value!r} outside [0,1]")
        clean[name] = value
    return clean


def predict_malicious(metrics: Dict[str, float], k: int = 3) -> Dict[str, Any]:
    """Return KNN-based malicious prediction for ``metrics``.

    Parameters
    ----------
    metrics:
        Mapping of feature name to value in the range [0, 1].
    k:
        Number of neighbours to consider.  Defaults to 3.

    Returns
    -------
    dict
        ``{"label": str, "confidence": float, "neighbors": list}``
    """
    if not _BASELINE:
        raise RuntimeError("No baseline training data available")

    metrics = _validate_metrics(metrics)
    if k <= 0:
        raise ValueError("k must be positive")

    neighbours = sorted(
        ((_distance(metrics, m), label) for m, label in _BASELINE),
        key=lambda x: x[0],
    )[:k]

    effective_k = len(neighbours)
    benign = sum(1 for _, label in neighbours if label == "benign")
    malicious = effective_k - benign
    label = "malicious" if malicious > benign else "benign"
    confidence = (
        round((malicious if label == "malicious" else benign) / effective_k, 2)
        if effective_k
        else 0.0
    )
    return {
        "label": label,
        "confidence": confidence,
        "neighbors": [
            {"distance": round(dist, 3), "label": lbl} for dist, lbl in neighbours
        ],
    }

__all__ = ["predict_malicious"]
