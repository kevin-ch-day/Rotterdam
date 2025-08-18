from device_analysis import package_scanner


def test_list_installed_packages_parses_output(monkeypatch):
    class FakeProc:
        stdout = "package:com.a\npackage:com.b\n"

    monkeypatch.setattr(package_scanner, "_run_adb", lambda *a, **k: FakeProc())
    monkeypatch.setattr(package_scanner, "_adb_path", lambda: "adb")

    pkgs = package_scanner.list_installed_packages("serial")
    assert pkgs == ["com.a", "com.b"]


def test_scan_for_dangerous_permissions(monkeypatch):
    monkeypatch.setattr(
        package_scanner,
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

    monkeypatch.setattr(package_scanner, "_get_permissions", fake_get_permissions)

    results = package_scanner.scan_for_dangerous_permissions("serial")
    assert results == [
        {
            "package": "com.a",
            "permissions": [
                "android.permission.CAMERA",
                "android.permission.READ_SMS",
            ],
        }
    ]

