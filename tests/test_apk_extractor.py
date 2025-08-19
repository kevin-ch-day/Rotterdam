import hashlib

from devices import apk


def test_acquire_apk_hashes_and_logs(tmp_path, monkeypatch):
    sample = tmp_path / "sample.apk"
    sample.write_bytes(b"hello")

    monkeypatch.setattr(apk, "pull_apk", lambda *a, **k: sample)

    class FakeDT:
        @staticmethod
        def utcnow():
            from datetime import datetime

            return datetime(2023, 1, 1, 0, 0, 0)

    monkeypatch.setattr(apk, "datetime", FakeDT)

    entry = apk.acquire_apk("SER", "com.app", operator="tester")

    assert entry["artifact"] == str(sample)
    assert entry["sha256"] == hashlib.sha256(b"hello").hexdigest()
    assert entry["timestamp"] == "2023-01-01T00:00:00Z"
    assert entry["operator"] == "tester"
