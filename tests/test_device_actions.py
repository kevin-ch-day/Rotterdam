import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.pop("platform", None)

from cli.actions.device import capture_screenshot


def test_capture_screenshot_creates_file(monkeypatch, tmp_path: Path):
    # Stub subprocess.run to write dummy PNG data
    def fake_run(cmd, check, stdout, timeout):
        stdout.write(b"data")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("cli.actions.device.subprocess.run", fake_run)

    # Redirect screenshot directory and filename
    monkeypatch.setattr("app_config.app_config.SCREENSHOTS_DIR", tmp_path)
    monkeypatch.setattr(
        "app_config.app_config.dated_filename",
        lambda p, s, d: tmp_path / "shot.png",
    )
    monkeypatch.setattr("app_config.app_config.ensure_dirs", lambda: None)

    capture_screenshot("serial123")

    assert (tmp_path / "shot.png").exists()
