import subprocess

import pytest

from devices import packages


def test_list_installed_packages_parses_output(monkeypatch):
    class FakeProc:
        stdout = "package:com.a\npackage:com.b\n"

    monkeypatch.setattr(packages, "_run_adb", lambda *a, **k: FakeProc())
    monkeypatch.setattr(packages, "_adb_path", lambda: "adb")

    pkgs = packages.list_installed_packages("serial")
    assert pkgs == ["com.a", "com.b"]


def test_list_installed_packages_error(monkeypatch):
    def fake_run(*a, **k):
        raise subprocess.CalledProcessError(1, a[0])

    monkeypatch.setattr(packages, "_run_adb", fake_run)
    monkeypatch.setattr(packages, "_adb_path", lambda: "adb")

    with pytest.raises(RuntimeError, match="Failed to list packages"):
        packages.list_installed_packages("serial")


def test_scan_for_dangerous_permissions(monkeypatch):
    monkeypatch.setattr(
        packages,
        "list_installed_packages",
        lambda serial: ["com.a", "com.b"],
    )

    def fake_get_permissions(serial, package):
        if package == "com.a":
            return [
                {"name": "android.permission.CAMERA", "granted": True, "category": "dangerous"},
                {"name": "android.permission.INTERNET", "granted": True, "category": "other"},
            ]
        return [
            {"name": "android.permission.INTERNET", "granted": True, "category": "other"}
        ]

    monkeypatch.setattr(packages, "_get_permissions", fake_get_permissions)

    results = packages.scan_for_dangerous_permissions("serial")
    assert results == [
        {
            "package": "com.a",
            "permissions": [
                {"name": "android.permission.CAMERA", "granted": True, "category": "dangerous"},
            ],
            "risk_flags": ["Internet"],
        }
    ]


def test_inventory_packages_collects_details(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    def fake_run(args, timeout=0):
        cmd = args[3:]
        if cmd == ["shell", "pm", "list", "packages", "-f", "-i"]:
            return Dummy(
                "package:/data/app/com.twitter/base.apk=com.twitter.android installer=com.android.vending\n"
                "package:/system/priv-app/Other/other.apk=com.other\n"
            )
        if cmd == ["shell", "dumpsys", "package", "com.twitter.android"]:
            return Dummy(
                "versionName=1.0\nversionCode=42 targetSdk=33\nuserId=10101\n"
            )
        if cmd == ["shell", "dumpsys", "package", "com.other"]:
            return Dummy(
                "versionName=2.0\nuserId=1000\npkgFlags=[ SYSTEM PRIVILEGED ]\n"
            )
        return Dummy("")

    monkeypatch.setattr(packages, "_run_adb", fake_run)
    monkeypatch.setattr(packages, "_adb_path", lambda: "adb")

    info = packages.inventory_packages("SER")
    assert info[0]["package"] == "com.twitter.android"
    assert info[0]["version_name"] == "1.0"
    assert info[0]["installer"] == "com.android.vending"
    assert info[0]["high_value"] is True
    assert info[0]["uid"] == "10101"
    assert info[0]["system"] is False
    assert info[0]["priv"] is False
    assert info[1]["package"] == "com.other"
    assert info[1]["high_value"] is False
    assert info[1]["system"] is True
    assert info[1]["priv"] is True
    assert info[1]["uid"] == "1000"


def test_export_permission_scan_writes_files(tmp_path):
    data = [
        {
            "package": "com.a",
            "permissions": [
                {"name": "android.permission.CAMERA", "granted": True, "category": "dangerous"}
            ],
            "risk_flags": ["Internet"],
        }
    ]
    json_p = tmp_path / "perm.json"
    csv_p = tmp_path / "perm.csv"
    packages.export_permission_scan(data, json_p, csv_p)
    assert json_p.exists()
    assert csv_p.exists()
    assert "com.a" in json_p.read_text()
    assert "com.a" in csv_p.read_text()


def test_get_permissions_includes_appops(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    def fake_run(args, timeout=0):
        cmd = args[3:]
        if cmd[:3] == ["shell", "dumpsys", "package"]:
            return Dummy(
                "uses-permission: android.permission.CAMERA\n"
                "android.permission.CAMERA: granted=true\n"
            )
        if cmd[:3] == ["shell", "cmd", "appops"]:
            return Dummy("CAMERA: allow\n")
        raise AssertionError("unexpected command")

    monkeypatch.setattr(packages, "_run_adb", fake_run)
    monkeypatch.setattr(packages, "_adb_path", lambda: "adb")

    perms = packages._get_permissions("SER", "com.a")
    assert perms == [
        {
            "name": "android.permission.CAMERA",
            "granted": True,
            "category": "dangerous",
            "mode": "allow",
        }
    ]

