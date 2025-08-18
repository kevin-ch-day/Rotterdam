from pathlib import Path

from device_analysis.apk_extractor import pull_apk
from device_analysis import apk_extractor


def test_pull_apk(monkeypatch, tmp_path):
    calls = []

    class Dummy:
        def __init__(self, stdout=""):
            self.stdout = stdout

    def fake_run(args, timeout=0):
        calls.append(args)
        if "pm" in args:
            return Dummy("package:/data/app/base.apk\n")
        return Dummy("")

    monkeypatch.setattr(apk_extractor, "_run_adb", fake_run)
    monkeypatch.setattr(apk_extractor, "_adb_path", lambda: "adb")

    out = pull_apk("SER", "pkg.name", dest_dir=str(tmp_path))
    assert out == Path(tmp_path) / "pkg.name.apk"
    assert calls[0][3:] == ["shell", "pm", "path", "pkg.name"]
    assert calls[1][3] == "pull"
