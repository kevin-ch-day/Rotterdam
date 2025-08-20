
from pathlib import Path
from sandbox import run_sandbox, collect_permissions, sniff_network, run_analysis


def test_run_sandbox(tmp_path: Path):
    apk = tmp_path / "app.apk"
    apk.write_text("fake")
    log, metrics, messages = run_sandbox(
        str(apk), tmp_path, hooks=["http_logger", "crypto_usage"]
    )
    assert log.exists()
    assert "app.apk" in log.read_text()
    assert messages
    assert metrics["network_endpoints"] == ["http://example.com"]


def test_collect_permissions(tmp_path: Path):
    apk = tmp_path / "app.apk"
    apk.write_text("fake")
    perms = collect_permissions(str(apk))
    assert "android.permission.INTERNET" in perms


def test_sniff_network(tmp_path: Path):
    apk = tmp_path / "app.apk"
    apk.write_text("fake")
    nets = sniff_network(str(apk))
    assert nets and nets[0]["destination"] == "example.com"


def test_run_analysis(tmp_path: Path):
    apk = tmp_path / "app.apk"
    apk.write_text("fake")
    result = run_analysis(str(apk), tmp_path)
    assert (tmp_path / "permissions.json").exists()
    assert (tmp_path / "network.json").exists()
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "messages.json").exists()
    assert result["permissions"]
    assert result["network"]
    assert result["messages"]
    assert "NETWORK:http://example.com" in result["messages"]
    assert result["metrics"]["network_endpoints"] == ["http://example.com"]


def test_run_analysis_disable_hook(tmp_path: Path):
    apk = tmp_path / "app.apk"
    apk.write_text("fake")
    result = run_analysis(str(apk), tmp_path, disable_hooks=["http_logger"])
    assert "NETWORK:http://example.com" not in result["messages"]
    assert result["metrics"]["network_endpoints"] == []
