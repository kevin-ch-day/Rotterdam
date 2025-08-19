"""Weighted risk scoring model for static and dynamic analysis metrics.

The scoring model uses a configurable set of metric weights. By default the
weights are tuned for a handful of high-signal static and dynamic indicators,
but callers may override them to experiment with alternate models.

Count-based metrics are normalized to the range [0, 1] using per-metric caps so
that weights are applied consistently regardless of the raw scale of each
metric.

Supported metrics (non-exhaustive):
  Static:
    - permission_density                (0..1)
    - component_exposure                (0..1)
    - untrusted_signature               (0 or 1; 1 = untrusted/missing)
    - cleartext_traffic_permitted       (0 or 1; 1 = cleartext allowed)
    - missing_certificate_pinning       (0 or 1; 1 = no pinning)
    - debug_overrides                   (0 or 1; 1 = debug overrides present)
    - expired_certificate               (0 or 1)
    - self_signed_certificate           (0 or 1)
    - vulnerable_dependency_count       (count; capped)
  Dynamic:
    - permission_invocation_count       (count; capped)
    - cleartext_endpoint_count          (count; capped)
    - file_write_count                  (count; capped)
    - malicious_endpoint_count          (count; capped)
"""

from __future__ import annotations

from typing import Any, Dict

# Default weights for metrics. These will be normalized to sum to 1.0
# inside calculate_risk_score so callers can provide partial overrides.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "permission_density": 0.23,
    "component_exposure": 0.15,
    "permission_invocation_count": 0.18,
    "cleartext_endpoint_count": 0.12,
    "file_write_count": 0.08,
    "malicious_endpoint_count": 0.09,
    "vulnerable_dependency_count": 0.10,
    "untrusted_signature": 0.05,
    # Network security flags
    "cleartext_traffic_permitted": 0.04,
    "missing_certificate_pinning": 0.03,
    "debug_overrides": 0.01,
    # Cert hygiene
    "expired_certificate": 0.04,
    "self_signed_certificate": 0.04,
}

# Normalization caps for count-based metrics. These are heuristic and prevent
# extremely large counts from dominating the score.
DEFAULT_CAPS: Dict[str, float] = {
    "permission_invocation_count": 50,
    "cleartext_endpoint_count": 10,
    "file_write_count": 100,
    "malicious_endpoint_count": 10,
    "vulnerable_dependency_count": 50,
}


def _normalize_count(value: float, cap: float) -> float:
    """Normalize value to [0, 1] using cap as an upper bound."""
    if cap <= 0:
        return 0.0
    if value <= 0:
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
        Metrics derived from static analysis such as `permission_density`,
        `component_exposure`, `untrusted_signature` (0 or 1),
        and `vulnerable_dependency_count` (count; capped).
    dynamic_metrics:
        Metrics from dynamic analysis such as permission invocation counts,
        cleartext/malicious endpoints, or file system writes.
    weights:
        Optional weighting overrides. Values are normalized so the final
        weights sum to 1.0.
    caps:
        Optional overrides for the normalization caps of count-based metrics.

    Returns
    -------
    dict
        {"score": float, "rationale": str, "breakdown": dict}
        - score: 0..100 inclusive
        - rationale: short human-readable explanation
        - breakdown: per-metric weighted contribution in percentage points
    """
    static_metrics = static_metrics or {}
    dynamic_metrics = dynamic_metrics or {}

    # Merge weights/caps with defaults and normalize weights to sum to 1.0.
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    total_weight = sum(weights.values()) or 1.0
    weights = {k: v / total_weight for k, v in weights.items()}
    caps = {**DEFAULT_CAPS, **(caps or {})}

    # Merge metrics for easier lookup.
    all_metrics: Dict[str, float] = {**static_metrics, **dynamic_metrics}

    score = 0.0
    breakdown: Dict[str, float] = {}

    # Compute normalized value for each metric (counts via caps; others assumed 0..1).
    for metric, weight in weights.items():
        raw = float(all_metrics.get(metric, 0.0))
        value = _normalize_count(raw, caps[metric]) if metric in caps else max(0.0, min(raw, 1.0))
        contrib = value * weight
        score += contrib
        # Store weighted contribution in percentage points for readability.
        breakdown[metric] = round(contrib * 100, 2)

    # Generate human-readable rationale using normalized/boolean indicators.
    pd = float(static_metrics.get("permission_density", 0.0))
    ce = float(static_metrics.get("component_exposure", 0.0))
    untrusted_sig = float(static_metrics.get("untrusted_signature", 0.0))
    cleartext_perm = float(static_metrics.get("cleartext_traffic_permitted", 0.0))
    missing_pinning = float(static_metrics.get("missing_certificate_pinning", 0.0))
    debug_over = float(static_metrics.get("debug_overrides", 0.0))
    expired_cert = float(static_metrics.get("expired_certificate", 0.0))
    self_signed = float(static_metrics.get("self_signed_certificate", 0.0))

    perm_inv_norm = _normalize_count(
        float(dynamic_metrics.get("permission_invocation_count", 0.0)),
        caps.get("permission_invocation_count", 1.0),
    )
    cleartext_norm = _normalize_count(
        float(dynamic_metrics.get("cleartext_endpoint_count", 0.0)),
        caps.get("cleartext_endpoint_count", 1.0),
    )
    file_writes_norm = _normalize_count(
        float(dynamic_metrics.get("file_write_count", 0.0)),
        caps.get("file_write_count", 1.0),
    )
    malicious_norm = _normalize_count(
        float(dynamic_metrics.get("malicious_endpoint_count", 0.0)),
        caps.get("malicious_endpoint_count", 1.0),
    )
    vulnerable_deps_norm = _normalize_count(
        float(static_metrics.get("vulnerable_dependency_count", 0.0)),
        caps.get("vulnerable_dependency_count", 1.0),
    )

    rationale_parts: list[str] = []
    if pd > 0.5:
        rationale_parts.append("elevated permission density")
    if ce > 0.5:
        rationale_parts.append("many exported components")
    if untrusted_sig >= 1.0:
        rationale_parts.append("untrusted or missing signature")
    if cleartext_perm >= 1.0:
        rationale_parts.append("cleartext traffic permitted")
    if missing_pinning >= 1.0:
        rationale_parts.append("missing certificate pinning")
    if debug_over >= 1.0:
        rationale_parts.append("debug network overrides present")
    if expired_cert >= 1.0:
        rationale_parts.append("expired signing certificate")
    if self_signed >= 1.0:
        rationale_parts.append("self-signed signing certificate")
    if perm_inv_norm > 0.5:
        rationale_parts.append("frequent permission use")
    if cleartext_norm > 0:
        rationale_parts.append("cleartext network endpoints detected")
    if malicious_norm > 0:
        rationale_parts.append("connections to known malicious endpoints")
    if file_writes_norm > 0:
        rationale_parts.append("file system writes observed")
    if vulnerable_deps_norm > 0:
        rationale_parts.append("known vulnerable dependencies found")

    rationale = "; ".join(rationale_parts) if rationale_parts else "no significant risk factors observed"

    return {
        "score": round(score * 100, 2),
        "rationale": rationale,
        "breakdown": breakdown,
    }
