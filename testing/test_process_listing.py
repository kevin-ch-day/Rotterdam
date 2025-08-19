import subprocess

import pytest

from device_analysis import process_listing


def test_list_processes_error(monkeypatch):
    monkeypatch.setattr(process_listing, "_adb_path", lambda: "adb")

    def fake_run(*a, **k):
        raise subprocess.CalledProcessError(1, a[0])

    monkeypatch.setattr(process_listing, "_run_adb", fake_run)

    with pytest.raises(RuntimeError, match="Failed to list processes"):
        process_listing.list_processes("SER")
