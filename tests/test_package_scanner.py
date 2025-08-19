import subprocess

import pytest

from devices import packages as device_packages
from apps import packages as app_packages


def test_list_installed_packages_parses_output(monkeypatch):
    class FakeProc:
        stdout = "package:com.a\npackage:com.b\n"

    monkeypatch.setattr(device_packages, "_run_adb", lambda *a, **k: FakeProc())
    monkeypatch.setattr(device_packages, "_adb_path", lambda: "adb")

    pkgs = device_packages.list_installed_packages("serial")
    assert pkgs == ["com.a", "com.b"]


def test_list_installed_packages_error(monkeypatch):
    def fake_run(*a, **k):
        raise subprocess.CalledProcessError(1, a[0])

    monkeypatch.setattr(device_packages, "_run_adb", fake_run)
    monkeypatch.setattr(device_packages, "_adb_path", lambda: "adb")

    with pytest.raises(RuntimeError, match="Failed to list packages"):
        device_packages.list_installed_packages("serial")


def test_scan_for_dangerous_permissions(monkeypatch):
    monkeypatch.setattr(
        device_packages,
        "list_installed_packages",
        lambda serial: ["com.a", "com.b"],
    )

    def fake_get_permissions(serial, package):
        if package == "com.a":
            return [
                "android.permission.CAMERA",
                "android.permission.READ_SMS",
            ]
        return ["android.permission.INTERNET"]

    monkeypatch.setattr(device_packages, "_get_permissions", fake_get_permissions)

    results = device_packages.scan_for_dangerous_permissions("serial")
    assert results == [
        {
            "package": "com.a",
            "permissions": [
                "android.permission.CAMERA",
                "android.permission.READ_SMS",
            ],
        }
    ]


def test_parse_pkg_list():
    text = "package:/data/a.apk=Com.A\npackage:/data/b.apk=com.b\n"
    mapping = app_packages.parse_pkg_list(text)
    assert mapping == {"com.a": "/data/a.apk", "com.b": "/data/b.apk"}


def test_parse_pkg_list_strips_whitespace():
    text = "package: /data/a.apk = COM.A \n"
    mapping = app_packages.parse_pkg_list(text)
    assert mapping == {"com.a": "/data/a.apk"}


def test_parse_pkg_list_handles_spaces_and_colons():
    text = (
        "package:/data/My App.apk=com.space\n"
        "package:/data/colon:app.apk=com.colon\n"
    )
    mapping = app_packages.parse_pkg_list(text)
    assert mapping == {
        "com.space": "/data/My App.apk",
        "com.colon": "/data/colon:app.apk",
    }


def test_parse_pkg_list_ignores_malformed():
    text = "garbage\npackage:/badline\npackage:/x=y=z\npackage:/ok.apk=com.ok\npackage:/broken=\n"
    mapping = app_packages.parse_pkg_list(text)
    assert mapping == {"com.ok": "/ok.apk"}


def test_normalize_inventory_collects_details(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    calls = []

    def fake_run(args, timeout=0):
        calls.append(timeout)
        cmd = args[3:]
        if cmd == ["shell", "pm", "list", "packages", "-f"]:
            return Dummy(
                "package:/data/app/com.twitter/base.apk=Com.Twitter.Android\n"
                "package:/data/app/com.other/base.apk=com.other\n"
            )
        if cmd == ["shell", "pm", "list", "packages", "-i"]:
            return Dummy(
                "package:com.twitter.android installer=com.android.vending\n"
            )
        if cmd == ["shell", "cmd", "package", "list", "packages", "-U"]:
            return Dummy(
                "package:com.twitter.android uid:10001\n"
                "package:com.other uid:10002\n"
            )
        if cmd == ["shell", "dumpsys", "package", "com.twitter.android"]:
            return Dummy("versionName=1.0\nflags=[ SYSTEM PRIVILEGED ]\n")
        if cmd == ["shell", "dumpsys", "package", "com.other"]:
            return Dummy("versionName=2.0\nflags=[ ]\n")
        return Dummy("")

    monkeypatch.setattr(app_packages, "_run_adb", fake_run)
    info = app_packages.normalize_inventory("adb", "SER")
    info_map = {p["package"]: p for p in info}

    t = info_map["com.twitter.android"]
    assert t["installer"] == "com.android.vending"
    assert t["uid"] == "10001"
    assert t["version"] == "1.0"
    assert t["system"] is True
    assert t["priv_app"] is True
    assert t["high_value"] is True

    o = info_map["com.other"]
    assert o["uid"] == "10002"
    assert o["installer"] == "unknown"
    assert o["system"] is False
    assert o["priv_app"] is False
    assert o["version"] == "2.0"
    assert o["high_value"] is False

    assert all(t == app_packages.DEFAULT_TIMEOUT for t in calls)


def test_normalize_inventory_handles_timeouts(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    def fake_run(args, timeout=0):
        cmd = args[3:]
        if cmd == ["shell", "pm", "list", "packages", "-f"]:
            return Dummy("package:/data/app/com.a/base.apk=com.a\n")
        if cmd == ["shell", "pm", "list", "packages", "-i"]:
            raise subprocess.TimeoutExpired(cmd, timeout)
        if cmd == ["shell", "cmd", "package", "list", "packages", "-U"]:
            return Dummy("package:com.a uid:1000\n")
        if cmd == ["shell", "dumpsys", "package", "com.a"]:
            return Dummy("")
        return Dummy("")

    monkeypatch.setattr(app_packages, "_run_adb", fake_run)
    info = app_packages.normalize_inventory("adb", "SER")
    assert info[0]["uid"] == "1000"
    assert info[0]["installer"] == "unknown"


def test_normalize_inventory_returns_empty_on_failure(monkeypatch):
    def fake_run(args, timeout=0):
        raise subprocess.TimeoutExpired(args, timeout)

    monkeypatch.setattr(app_packages, "_run_adb", fake_run)
    assert app_packages.normalize_inventory("adb", "SER") == []


def test_normalize_inventory_fast_skips_dumpsys(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    def fake_run(args, timeout=0):
        cmd = args[3:]
        if cmd == ["shell", "pm", "list", "packages", "-f"]:
            return Dummy("package:/system/priv-app/p.apk=com.a\n")
        if cmd == ["shell", "pm", "list", "packages", "-i"]:
            return Dummy("package:com.a installer=store\n")
        if cmd == ["shell", "cmd", "package", "list", "packages", "-U"]:
            return Dummy("package:com.a uid:1000\n")
        assert cmd != ["shell", "dumpsys", "package", "com.a"]
        return Dummy("")

    monkeypatch.setattr(app_packages, "_run_adb", fake_run)
    info = app_packages.normalize_inventory("adb", "SER", fast=True)
    assert info[0]["version"] == "unknown"
    assert info[0]["system"] is True
    assert info[0]["priv_app"] is True


def test_normalize_inventory_returns_sorted(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    def fake_run(args, timeout=0):
        cmd = args[3:]
        if cmd == ["shell", "pm", "list", "packages", "-f"]:
            return Dummy("package:/a.apk=z\npackage:/b.apk=a\n")
        return Dummy("")

    monkeypatch.setattr(app_packages, "_run_adb", fake_run)
    info = app_packages.normalize_inventory("adb", "SER", fast=True)
    assert [p["package"] for p in info] == ["a", "z"]


def test_normalize_inventory_disables_dumpsys_after_failure(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    calls = []

    def fake_run(args, timeout=0):
        cmd = args[3:]
        if cmd == ["shell", "pm", "list", "packages", "-f"]:
            return Dummy("package:/a.apk=a\npackage:/b.apk=b\n")
        if cmd == ["shell", "pm", "list", "packages", "-i"]:
            return Dummy("")
        if cmd == ["shell", "cmd", "package", "list", "packages", "-U"]:
            return Dummy("")
        if cmd == ["shell", "dumpsys", "package", "a"]:
            calls.append("a")
            raise subprocess.TimeoutExpired(cmd, timeout)
        if cmd == ["shell", "dumpsys", "package", "b"]:
            calls.append("b")
            return Dummy("versionName=1\n")
        return Dummy("")

    monkeypatch.setattr(app_packages, "_run_adb", fake_run)
    info = app_packages.normalize_inventory("adb", "SER")
    assert calls == ["a"]
    assert all(p["version"] == "unknown" for p in info)


def test_normalize_inventory_restarts_adb_server(monkeypatch):
    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    calls = []

    def fake_run(args, timeout=0):
        calls.append(args)
        cmd = args[3:]
        if args[:2] == ["adb", "start-server"]:
            return Dummy("")
        if cmd == ["shell", "pm", "list", "packages", "-f"]:
            if len(calls) == 1:
                raise subprocess.CalledProcessError(1, args)
            return Dummy("package:/x.apk=x\n")
        if cmd == ["shell", "pm", "list", "packages", "-i"]:
            return Dummy("")
        if cmd == ["shell", "cmd", "package", "list", "packages", "-U"]:
            return Dummy("")
        return Dummy("")

    monkeypatch.setattr(app_packages, "_run_adb", fake_run)
    info = app_packages.normalize_inventory("adb", "SER", fast=True)
    assert [p["package"] for p in info] == ["x"]
    assert ["adb", "start-server"] in calls
