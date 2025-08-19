import subprocess

import pytest

from devices import processes


def test_list_processes_error(monkeypatch):
    monkeypatch.setattr(processes, "_adb_path", lambda: "adb")

    def fake_run(*a, **k):
        raise subprocess.CalledProcessError(1, a[0])

    monkeypatch.setattr(processes, "_run_adb", fake_run)

    with pytest.raises(RuntimeError, match="Failed to list processes"):
        processes.list_processes("SER")
