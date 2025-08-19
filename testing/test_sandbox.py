from pathlib import Path
from sandbox import run_sandbox, collect_permissions, sniff_network, analyze_apk


def test_run_sandbox(tmp_path: Path):
    log = run_sandbox("/tmp/app.apk", tmp_path)
    assert log.exists()
    assert "app.apk" in log.read_text()


def test_collect_permissions():
    perms = collect_permissions("/tmp/app.apk")
    assert "android.permission.INTERNET" in perms


def test_sniff_network():
    nets = sniff_network("/tmp/app.apk")
    assert nets and nets[0]["destination"] == "example.com"


def test_analyze_apk(tmp_path: Path):
    result = analyze_apk("/tmp/app.apk", tmp_path)
    assert (tmp_path / "permissions.json").exists()
    assert (tmp_path / "network.json").exists()
    assert result["permissions"]
    assert result["network"]
