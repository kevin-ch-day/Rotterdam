import pytest

from analysis.ml_model import predict_malicious


def test_predict_malicious_flags_high_risk():
    metrics = {"permission_density": 0.9, "component_exposure": 0.85, "cleartext_traffic_permitted": 1}
    result = predict_malicious(metrics)
    assert result["label"] == "malicious"
    assert 0 <= result["confidence"] <= 1
    assert result["neighbors"]


def test_predict_malicious_rejects_invalid_metrics():
    with pytest.raises(ValueError):
        predict_malicious({"permission_density": 1.5})
