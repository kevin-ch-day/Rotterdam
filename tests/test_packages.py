import subprocess
import sys
from pathlib import Path

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.pop("platform", None)

from platform.android.devices import packages


def test_inventory_packages_categorises_and_scores(monkeypatch):
    list_output = (
        "package:/data/app/com.whatsapp/base.apk=com.whatsapp installer=com.android.vending\n"
    )
    dumpsys_output = (
        "package: com.whatsapp\n"
        "versionName=2.0\n"
        "versionCode=200\n"
        "uid=1000\n"
        "uses-permission:android.permission.RECORD_AUDIO\n"
        "uses-permission:android.permission.READ_SMS\n"
    )

    def fake_run(args, timeout=10):
        cmd = " ".join(args)
        if "pm list packages" in cmd:
            return subprocess.CompletedProcess(args, 0, stdout=list_output, stderr="")
        if "dumpsys package com.whatsapp" in cmd:
            return subprocess.CompletedProcess(args, 0, stdout=dumpsys_output, stderr="")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(packages, "_run_adb", fake_run)

    result = packages.inventory_packages("serial123")
    assert result
    app = result[0]
    assert app["package"] == "com.whatsapp"
    # Categorised as Messaging and assigned risk score (2 perms + high value)
    assert "Messaging" in app["categories"]
    assert app["risk_score"] == 3
    assert sorted(app["dangerous_permissions"]) == [
        "android.permission.READ_SMS",
        "android.permission.RECORD_AUDIO",
    ]
