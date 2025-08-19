from risk_scoring import calculate_risk_score


def test_calculate_risk_score_outputs_score_and_rationale():
    static = {"permission_density": 0.6, "component_exposure": 0.4}
    dynamic = {
        "permission_invocation_count": 20,
        "cleartext_endpoint_count": 1,
        "file_write_count": 5,
    }
    result = calculate_risk_score(static, dynamic)
    assert 0 <= result["score"] <= 100
    assert isinstance(result["rationale"], str)
    assert result["rationale"]
    assert "breakdown" in result and "permission_density" in result["breakdown"]


def test_weights_can_be_overridden():
    static = {"permission_density": 0.8, "component_exposure": 0.0}
    default = calculate_risk_score(static)
    # Heavily emphasise permission density
    override = calculate_risk_score(static, weights={"permission_density": 10.0})
    assert override["score"] > default["score"]
