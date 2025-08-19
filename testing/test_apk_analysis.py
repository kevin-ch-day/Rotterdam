from pathlib import Path

from apk_analysis import (
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
)


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
    report = write_report(
        tmp_path,
        ["android.permission.INTERNET"],
        perm_details,
        ["Sample.java:10"],
        comps,
        {"minSdkVersion": 21},
        [{"name": "android.hardware.camera", "required": False}],
        {"debuggable": True},
        metadata,
    )
    data = report.read_text()
    assert "android.permission.INTERNET" in data
    assert "Sample.java:10" in data
    assert "Main" in data
    assert "minSdkVersion" in data
    assert "android.hardware.camera" in data
    assert "debuggable" in data
    assert "com.example.API_KEY" in data
