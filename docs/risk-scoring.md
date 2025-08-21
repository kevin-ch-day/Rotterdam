# Risk Scoring Model

The scoring engine in `platform/android/analysis/static/scoring/risk_score.py` combines static and dynamic metrics into a normalized 0–100 risk score.

The previous `analysis/risk_scoring` helper package has been archived under
`analysis/archived/`.

## Metrics and Weights

Default metric weights are tuned for common risk indicators. Values are normalized internally so weights sum to 1.0.

| Metric | Default Weight |
| --- | --- |
| permission_density | 0.23 |
| component_exposure | 0.15 |
| permission_invocation_count | 0.18 |
| cleartext_endpoint_count | 0.12 |
| file_write_count | 0.08 |
| malicious_endpoint_count | 0.09 |
| vulnerable_dependency_count | 0.10 |
| untrusted_signature | 0.05 |
| ml_pred_malicious | 0.05 |
| cleartext_traffic_permitted | 0.04 |
| missing_certificate_pinning | 0.03 |
| debug_overrides | 0.01 |
| expired_certificate | 0.04 |
| self_signed_certificate | 0.04 |

Count-based metrics are capped before weighting to prevent a single large value from dominating the score. For example, `permission_invocation_count` is capped at 50 calls.

## Customizing Weights

Callers may supply alternative weights or caps:

```python
from platform.android.analysis.static.scoring.risk_score import calculate_risk_score

static_metrics = {"permission_density": 0.6}

custom_weights = {"permission_density": 0.5, "component_exposure": 0.5}
result = calculate_risk_score(static_metrics, weights=custom_weights)
print(result["score"], result["rationale"])
```

Only the provided keys are overridden; unspecified metrics use defaults. This allows experimentation with different scoring strategies.
