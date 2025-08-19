import pytest
from pathlib import Path

from analysis.yara_scan import compile_rules, scan_directory

# Robustly skip if yara or its native library can't load.
# Some environments raise OSError/AttributeError instead of ImportError.
try:  # pragma: no cover - environment-dependent import guard
    import yara  # type: ignore  # noqa: F401
except Exception:
    pytest.skip("yara library unavailable", allow_module_level=True)


def test_scan_directory(tmp_path: Path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "test.yar").write_text(
        'rule Dummy { strings: $a = "test" condition: $a }'
    )

    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "sample.txt").write_text("this is a test")

    rules = compile_rules(rules_dir)
    matches = scan_directory(files_dir, rules=rules)

    assert matches["sample.txt"] == ["Dummy"]
