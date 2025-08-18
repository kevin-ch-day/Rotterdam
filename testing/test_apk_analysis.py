from pathlib import Path

from apk_analysis import extract_permissions, scan_for_secrets, write_report


def test_extract_permissions():
    manifest = (
        '<manifest>'
        '<uses-permission android:name="android.permission.INTERNET"/>'
        '<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>'
        '</manifest>'
    )
    perms = extract_permissions(manifest)
    assert perms == [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.INTERNET",
    ]


def test_scan_for_secrets(tmp_path: Path):
    sample = tmp_path / "Sample.java"
    sample.write_text("String API_KEY = \"abc\";")
    results = scan_for_secrets(tmp_path)
    assert results and "Sample.java" in results[0]


def test_write_report(tmp_path: Path):
    report = write_report(tmp_path, ["android.permission.INTERNET"], ["Sample.java:10"])
    data = report.read_text()
    assert "android.permission.INTERNET" in data
    assert "Sample.java:10" in data
