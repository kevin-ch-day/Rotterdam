from pathlib import Path

from analysis import secrets
from analysis.secrets import (
    _contains_nul_bytes,
    _is_text_file,
    _load_text,
    _shannon_entropy,
    scan_for_secrets,
)


def test_shannon_entropy():
    assert _shannon_entropy("") == 0.0
    assert _shannon_entropy("aaaa") == 0.0
    assert round(_shannon_entropy("abcd"), 3) == 2.0


def test_is_text_file():
    assert _is_text_file(Path("file.txt"))
    assert not _is_text_file(Path("file.exe"))


def test_contains_nul_bytes():
    assert _contains_nul_bytes(b"a\x00b")
    assert not _contains_nul_bytes(b"abc")


def test_load_text_filters(tmp_path: Path, monkeypatch):
    text_file = tmp_path / "sample.txt"
    text_file.write_text("hello")
    assert _load_text(text_file) == "hello"

    bin_file = tmp_path / "bin.txt"
    bin_file.write_bytes(b"\x00\x01")
    assert _load_text(bin_file) is None

    big_file = tmp_path / "big.txt"
    big_file.write_text("x" * 10)
    monkeypatch.setattr(secrets, "SIZE_LIMIT", 5)
    assert _load_text(big_file) is None


def test_scan_for_secrets_detects_keyword_and_entropy(tmp_path: Path):
    token = "0123456789abcdefABCDEFghijkl"
    # ensure our token has high entropy so entropy detector triggers
    assert _shannon_entropy(token) > 4.5
    test_file = tmp_path / "config.txt"
    test_file.write_text(f"API_KEY=foo\n{token}\n")

    results = scan_for_secrets(tmp_path)
    assert f"{test_file.name}:0" in results
    assert f"{test_file.name}:12" in results
