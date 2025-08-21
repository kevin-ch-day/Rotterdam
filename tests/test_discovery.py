import subprocess
import sys
from pathlib import Path

# Ensure project root is first on sys.path so 'platform' package is found
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules.pop("platform", None)

from platform.android.devices import discovery


def test_restart_adb_on_failure(monkeypatch):
    calls = []

    def fake_run(args, timeout=8):
        calls.append(args)
        if len(calls) == 1:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0, stdout="List of devices attached\n1234 device\n", stderr="")

    monkeypatch.setattr(discovery, "_adb_path", lambda: "adb")
    monkeypatch.setattr(discovery, "_run_adb", fake_run)

    discovery.check_connected_devices()

    assert calls == [
        ["adb", "devices", "-l"],
        ["adb", "kill-server"],
        ["adb", "start-server"],
        ["adb", "devices", "-l"],
    ]


def test_no_devices_prints_fedora_hint(monkeypatch, capsys):
    def fake_run(args, timeout=8):
        return subprocess.CompletedProcess(args, 0, stdout="List of devices attached\n", stderr="")

    monkeypatch.setattr(discovery, "_adb_path", lambda: "adb")
    monkeypatch.setattr(discovery, "_run_adb", fake_run)

    discovery.check_connected_devices()
    out = capsys.readouterr().out
    assert "SUBSYSTEM==\"usb\"" in out
    assert "SELinux" in out
    assert "ANDROID_ANALYSIS_SETUP.md" in out

