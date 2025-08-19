"""Weighted risk scoring model for static and dynamic analysis metrics.

The scoring model uses a configurable set of metric weights.  By default the
weights are tuned for a handful of high‑signal static and dynamic indicators but
callers may override them to experiment with alternate models.  Count‑based
metrics are normalised to the range ``[0, 1]`` using per‑metric caps so that
weights are applied consistently regardless of the raw scale of each metric.
"""

from __future__ import annotations

from typing import Any, Dict

# Default weights for metrics.  These will be normalised to sum to ``1.0``
# inside :func:`calculate_risk_score` so callers can provide partial overrides
# without worrying about the sum of the values.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "permission_density": 0.3,
    "component_exposure": 0.2,
    "permission_invocation_count": 0.2,
    "cleartext_endpoint_count": 0.2,
    "file_write_count": 0.1,
    "vulnerable_dependency_count": 0.1,
}

# Normalisation caps for count based metrics.  The selected caps are heuristic
# and merely prevent extremely large counts from dominating the score.
DEFAULT_CAPS: Dict[str, float] = {
    "permission_invocation_count": 50,
    "cleartext_endpoint_count": 10,
    "file_write_count": 100,
    "vulnerable_dependency_count": 50,
}


def _normalize_count(value: float, cap: float) -> float:
    """Normalize ``value`` to ``[0, 1]`` using ``cap`` as an upper bound."""
    if cap <= 0:
        return 0.0
    return min(value / cap, 1.0)


def calculate_risk_score(
    static_metrics: Dict[str, float] | None = None,
    dynamic_metrics: Dict[str, float] | None = None,
    *,
    weights: Dict[str, float] | None = None,
    caps: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """Return a risk score and rationale based on analysis metrics.

    Parameters
    ----------
    static_metrics:
        Metrics derived from static analysis such as ``permission_density``
        and ``component_exposure``.
    dynamic_metrics:
        Metrics from dynamic analysis such as permission invocation counts,
        cleartext network endpoints, or file system writes.
    weights:
        Optional weighting overrides.  Values are normalised so the final
        weights sum to ``1.0``.
    caps:
        Optional overrides for the normalisation caps of count based metrics.

    Returns
    -------
    dict
        ``{"score": float, "rationale": str, "breakdown": dict}``
    """

    static_metrics = static_metrics or {}
    dynamic_metrics = dynamic_metrics or {}

    # Merge weights/caps with defaults and normalise weights to sum to 1.0.
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    total_weight = sum(weights.values()) or 1.0
    weights = {k: v / total_weight for k, v in weights.items()}
    caps = {**DEFAULT_CAPS, **(caps or {})}

    # Merge metrics for easier lookup.
    all_metrics: Dict[str, float] = {**static_metrics, **dynamic_metrics}

    score = 0.0
    breakdown: Dict[str, float] = {}
    for metric, weight in weights.items():
        value = float(all_metrics.get(metric, 0.0))
        if metric in caps:
            value = _normalize_count(value, caps[metric])
        score += value * weight
        breakdown[metric] = round(value * weight * 100, 2)

    # Generate human readable rationale using heuristic thresholds for the
    # default metrics.  These can be expanded as additional metrics are added.
    pd = float(static_metrics.get("permission_density", 0.0))
    ce = float(static_metrics.get("component_exposure", 0.0))
    perm_inv = float(dynamic_metrics.get("permission_invocation_count", 0.0))
    cleartext = float(dynamic_metrics.get("cleartext_endpoint_count", 0.0))
    file_writes = float(dynamic_metrics.get("file_write_count", 0.0))
    vulnerable_deps = float(static_metrics.get("vulnerable_dependency_count", 0.0))

    rationale_parts: list[str] = []
    if pd > 0.5:
        rationale_parts.append("elevated permission density")
    if ce > 0.5:
        rationale_parts.append("many exported components")
    if perm_inv > 10:
        rationale_parts.append("frequent permission use")
    if cleartext > 0:
        rationale_parts.append("cleartext network endpoints detected")
    if file_writes > 0:
        rationale_parts.append("file system writes observed")
    if vulnerable_deps > 0:
        rationale_parts.append("known vulnerable dependencies found")

    rationale = (
        "; ".join(rationale_parts)
        if rationale_parts
        else "no significant risk factors observed"
    )

    return {
        "score": round(score * 100, 2),
        "rationale": rationale,
        "breakdown": breakdown,
    }
