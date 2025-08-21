import os
import stat
from pathlib import Path

import logging
import pytest

import settings
from cli.actions import health


def test_invalid_port_defaults(monkeypatch, caplog):
    monkeypatch.setenv("APP_PORT", "not-a-number")
    settings.get_settings.cache_clear()
    with caplog.at_level(logging.WARNING):
        s = settings.get_settings()
    assert s.port == settings.legacy.DEFAULT_PORT
    assert "APP_PORT" in caplog.text


def test_host_empty_defaults(monkeypatch, caplog):
    monkeypatch.setenv("APP_HOST", "")
    settings.get_settings.cache_clear()
    with caplog.at_level(logging.WARNING):
        s = settings.get_settings()
    assert s.host == settings.legacy.DEFAULT_HOST
    assert "APP_HOST empty" in caplog.text


@pytest.mark.parametrize("val", ["1", "true", "yes", "on", "TRUE", "On"])
def test_open_browser_parsing(monkeypatch, val):
    monkeypatch.setenv("OPEN_BROWSER", val)
    monkeypatch.setenv("DISPLAY", ":0")
    settings.get_settings.cache_clear()
    assert settings.get_settings().open_browser is True


def test_open_browser_headless(monkeypatch, caplog):
    monkeypatch.setenv("OPEN_BROWSER", "yes")
    monkeypatch.delenv("DISPLAY", raising=False)
    settings.get_settings.cache_clear()
    with caplog.at_level(logging.INFO):
        assert settings.get_settings().open_browser is False
    assert "no DISPLAY" in caplog.text


def test_open_browser_non_loopback(monkeypatch, caplog):
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    monkeypatch.setenv("OPEN_BROWSER", "yes")
    monkeypatch.setenv("DISPLAY", ":0")
    settings.get_settings.cache_clear()
    with caplog.at_level(logging.INFO):
        s = settings.get_settings()
    assert s.open_browser is False
    assert "non-loopback" in caplog.text


def _make_exec(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_adb_env_precedence(monkeypatch, tmp_path):
    fake = _make_exec(tmp_path / "env" / "adb")
    monkeypatch.setenv("ADB", str(fake))
    monkeypatch.setenv("DISPLAY", ":0")
    settings.get_settings.cache_clear()
    assert settings.get_settings().adb_bin == str(fake)


def test_adb_fedora_default(monkeypatch, tmp_path):
    fedora = _make_exec(tmp_path / "Android" / "Sdk" / "platform-tools" / "adb")
    monkeypatch.delenv("ADB", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "")
    settings.get_settings.cache_clear()
    assert settings.get_settings().adb_bin == str(fedora)


def test_adb_path_lookup(monkeypatch, tmp_path):
    monkeypatch.delenv("ADB", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    fake = _make_exec(tmp_path / "bin" / "adb")
    monkeypatch.setenv("PATH", str(fake.parent))
    settings.get_settings.cache_clear()
    assert settings.get_settings().adb_bin == str(fake)


def test_health_check_reports_missing_adb(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("ADB", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "")
    settings.get_settings.cache_clear()
    monkeypatch.setattr(health, "_check_database", lambda: (True, "ok"))
    monkeypatch.setattr(health, "_check_module", lambda name: (True, "ok"))
    monkeypatch.setattr(health, "_check_binary", lambda name: (True, "ok"))
    health.run_health_check()
    captured = capsys.readouterr()
    text = (captured.out + captured.err).lower()
    assert "adb missing" in text
