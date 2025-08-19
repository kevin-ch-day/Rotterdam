import subprocess
from types import SimpleNamespace

from sandbox.ui_driver import run_monkey


def test_run_monkey_parses_activity(monkeypatch):
    sample_output = """
    Monkey: seed=123 count=2
    ActivityManager: Start proc 123:cmp=com.example/.MainActivity
    Activity: com.example/.SettingsActivity
    """

    def fake_run(cmd, stdout, stderr, text, check):
        return SimpleNamespace(stdout=sample_output)

    monkeypatch.setattr(subprocess, "run", fake_run)

    acts = run_monkey("serial", "com.example", event_count=2)
    assert acts == [
        "com.example/.MainActivity",
        "com.example/.SettingsActivity",
    ]
