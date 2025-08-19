from reports import ieee


def test_format_device_inventory_creates_section_and_table():
    devices = [
        {
            "serial": "ABC123",
            "model": "Pixel",
            "android_release": "14",
            "trust": "high",
        }
    ]
    out = ieee.format_device_inventory(devices)
    assert "SECTION I: DEVICE ENUMERATION" in out
    assert "I.A – Detecting Connected Devices" in out
    assert "Table I. Connected Devices" in out
    assert "Observation:" in out
    assert "ABC123" in out


def test_format_package_inventory_heading_and_caption():
    packages = [
        {
            "package": "com.twitter.android",
            "version_name": "9.0",
            "installer": "com.android.vending",
            "high_value": True,
        }
    ]
    out = ieee.format_package_inventory(packages)
    assert "SECTION II: APPLICATION INVENTORY" in out
    assert "II.A – Application Discovery" in out
    assert "Table II. Installed Applications" in out
    assert "Observation:" in out
    assert "com.twitter.android" in out
    assert "yes" in out


def test_format_evidence_log_outputs_section_and_table():
    entries = [
        {
            "artifact": "file.apk",
            "sha256": "abc",
            "timestamp": "2023-01-01T00:00:00Z",
            "operator": "tester",
        }
    ]
    out = ieee.format_evidence_log(entries)
    assert "SECTION III: EVIDENCE LOG" in out
    assert "III.A – Acquisition Evidence" in out
    assert "Table III. Acquisition Evidence" in out
    assert "Observation:" in out
    assert "file.apk" in out


def test_format_risk_summary_includes_score_and_breakdown():
    risk = {
        "score": 42.5,
        "rationale": "Example rationale",
        "breakdown": {"permission_density": 12.3},
    }
    out = ieee.format_risk_summary(risk)
    assert "SECTION IV: RISK ASSESSMENT" in out
    assert "IV.A – Aggregated Risk Score" in out
    assert "Table IV. Risk Breakdown" in out
    assert "42.5" in out
    assert "Example rationale" in out

