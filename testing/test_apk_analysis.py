from pathlib import Path
import json

from analysis import (
    extract_permissions,
    extract_permission_details,
    extract_components,
    extract_sdk_info,
    extract_features,
    extract_app_flags,
    extract_metadata,
    categorize_permissions,
    scan_for_secrets,
    write_report,
    calculate_derived_metrics,
)
from sandbox import compute_runtime_metrics
from risk_scoring import calculate_risk_score


def test_extract_permissions():
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<uses-permission android:name="android.permission.INTERNET"/>'
        '<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>'
        '</manifest>'
    )
    perms = extract_permissions(manifest)
    assert perms == [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.INTERNET",
    ]


def test_extract_permission_details():
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<uses-permission android:name="android.permission.CAMERA" android:maxSdkVersion="28"/>'
        '<uses-permission-sdk-23 android:name="android.permission.READ_CONTACTS"/>'
        '</manifest>'
    )
    details = extract_permission_details(manifest)
    assert {
        "name": "android.permission.CAMERA",
        "tag": "uses-permission",
        "max_sdk_version": 28,
    } in details
    assert any(d["tag"] == "uses-permission-sdk-23" and d["name"] == "android.permission.READ_CONTACTS" for d in details)


def test_categorize_permissions():
    perms = [
        {"name": "android.permission.INTERNET", "tag": "uses-permission", "max_sdk_version": None},
        {"name": "android.permission.READ_CONTACTS", "tag": "uses-permission", "max_sdk_version": None},
    ]
    details = categorize_permissions(perms)
    assert any(d["name"] == "android.permission.READ_CONTACTS" and d["dangerous"] for d in details)
    assert any(d["name"] == "android.permission.INTERNET" and not d["dangerous"] for d in details)


def test_scan_for_secrets(tmp_path: Path):
    sample = tmp_path / "Sample.java"
    sample.write_text("String API_KEY = \"abc\";")
    results = scan_for_secrets(tmp_path)
    assert results and "Sample.java" in results[0]


def test_extract_components():
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<application>'
        '<activity android:name="MainActivity" android:exported="true" />'
        '<service android:name="MyService" android:permission="com.example.PERMISSION" />'
        '</application>'
        '</manifest>'
    )
    comps = extract_components(manifest)
    assert comps["activity"][0]["name"] == "MainActivity"
    assert comps["activity"][0]["exported"] is True
    assert comps["service"][0]["permission"] == "com.example.PERMISSION"


def test_extract_sdk_info():
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<uses-sdk android:minSdkVersion="21" android:targetSdkVersion="30" />'
        '</manifest>'
    )
    info = extract_sdk_info(manifest)
    assert info["minSdkVersion"] == 21
    assert info["targetSdkVersion"] == 30


def test_extract_features():
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<uses-feature android:name="android.hardware.camera" android:required="false" />'
        '</manifest>'
    )
    features = extract_features(manifest)
    assert features[0]["name"] == "android.hardware.camera"
    assert features[0]["required"] is False


def test_extract_app_flags():
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<application android:debuggable="true" android:allowBackup="false" android:usesCleartextTraffic="true" />'
        '</manifest>'
    )
    flags = extract_app_flags(manifest)
    assert flags["debuggable"] is True
    assert flags["allowBackup"] is False
    assert flags["usesCleartextTraffic"] is True


def test_extract_metadata():
    manifest = (
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<application>'
        '<meta-data android:name="com.example.API_KEY" android:value="123" />'
        '</application>'
        '</manifest>'
    )
    data = extract_metadata(manifest)
    assert data == [{"name": "com.example.API_KEY", "value": "123"}]


def test_write_report(tmp_path: Path):
    comps = {"activity": [{"name": "Main", "exported": False, "permission": ""}]}
    perm_details = [
        {
            "name": "android.permission.INTERNET",
            "tag": "uses-permission",
            "max_sdk_version": None,
            "dangerous": False,
        }
    ]
    metadata = [{"name": "com.example.API_KEY", "value": "123"}]
    runtime_metrics = compute_runtime_metrics(
        ["android.permission.INTERNET"],
        ["https://example.com"],
        ["/data/a.txt"],
    )
    metrics = calculate_derived_metrics(
        perm_details,
        comps,
        {"minSdkVersion": 21, "targetSdkVersion": 30},
        [{"name": "android.hardware.camera", "required": False}],
        metadata,
        runtime_metrics,
    )
    risk = calculate_risk_score(metrics, {})
    report = write_report(
        tmp_path,
        ["android.permission.INTERNET"],
        perm_details,
        ["Sample.java:10"],
        comps,
        {"minSdkVersion": 21, "targetSdkVersion": 30},
        [{"name": "android.hardware.camera", "required": False}],
        {"debuggable": True},
        metadata,
        metrics,
        risk,
        {"Sample.java": ["TestRule"]},
    )
    data = json.loads(report.read_text())
    assert "android.permission.INTERNET" in str(data)
    assert "Sample.java:10" in str(data)
    assert "Main" in str(data)
    assert "minSdkVersion" in str(data)
    assert "android.hardware.camera" in str(data)
    assert "debuggable" in str(data)
    assert "com.example.API_KEY" in str(data)
    assert "permission_density" in str(data)
    assert "feature_count" in str(data)
    assert "risk" in str(data)
    assert "rationale" in str(data)
    assert "permission_prefix_counts" in data["metrics"]
    assert data["yara_matches"]["Sample.java"] == ["TestRule"]


def test_calculate_derived_metrics():
    perm_details = [
        {"name": "android.permission.INTERNET", "dangerous": False},
        {"name": "android.permission.READ_CONTACTS", "dangerous": True},
    ]
    comps = {
        "activity": [
            {"name": "MainActivity", "exported": True, "permission": ""},
            {"name": "OtherActivity", "exported": False, "permission": ""},
        ],
        "service": [],
        "receiver": [],
        "provider": [],
    }
    sdk_info = {"minSdkVersion": 21, "targetSdkVersion": 30}
    features = [{"name": "android.hardware.camera", "required": False}]
    metadata = [{"name": "com.example.API_KEY", "value": "123"}]
    runtime_metrics = {
        "permission_usage_counts": {"android.permission.INTERNET": 3},
        "network_endpoints": ["https://example.com"],
        "filesystem_writes": ["/data/a.txt"],
    }
    metrics = calculate_derived_metrics(
        perm_details, comps, sdk_info, features, metadata, runtime_metrics
    )
    assert metrics["permission_density"] == 0.5
    assert metrics["component_exposure"] == 0.5
    assert metrics["total_permission_count"] == 2
    assert metrics["dangerous_permission_count"] == 1
    assert metrics["total_component_count"] == 2
    assert metrics["exported_component_count"] == 1
    assert metrics["feature_count"] == 1
    assert metrics["metadata_count"] == 1
    assert metrics["min_sdk"] == 21
    assert metrics["target_sdk"] == 30
    assert metrics["runtime_permission_count"] == 1
    assert metrics["unused_permission_count"] == 1
    assert metrics["runtime_permission_coverage"] == 0.5
    assert metrics["network_endpoint_count"] == 1
    assert metrics["filesystem_write_count"] == 1
    assert metrics["sdk_span"] == 9
    assert metrics["permission_prefix_counts"]["READ"] == 1
