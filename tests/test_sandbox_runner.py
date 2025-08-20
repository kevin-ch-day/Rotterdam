from pathlib import Path

import pytest

from rotterdam.android.analysis.dynamic.runner import run_sandbox


def test_run_sandbox_raises_for_missing_apk(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        run_sandbox(str(tmp_path / "missing.apk"), tmp_path)


def test_run_sandbox_collects_metrics(tmp_path: Path) -> None:
    apk = tmp_path / "dummy.apk"
    apk.write_text("fake")

    log, metrics, messages = run_sandbox(str(apk), tmp_path, hooks=["crypto_usage", "http_logger"])
    assert log.exists()
    # instrumentation should yield at least one event for each category
    assert metrics["network_endpoint_count"] == 1
    assert metrics["filesystem_write_count"] == 1
    assert metrics["unique_permission_count"] == 1
    assert messages
