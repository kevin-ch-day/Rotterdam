from pathlib import Path

import pytest

from analysis.yara_scan import compile_rules, scan_directory


try:  # pragma: no cover - depends on optional system library
    import yara  # type: ignore
except Exception:  # noqa: F401 - the variable is used in pytestmark below
    yara = None

pytestmark = pytest.mark.skipif(yara is None, reason="yara library not available")


def test_scan_directory(tmp_path: Path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "test.yar").write_text(
        "rule Dummy { strings: $a = \"test\" condition: $a }"
    )
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "sample.txt").write_text("this is a test")
    rules = compile_rules(rules_dir)
    matches = scan_directory(files_dir, rules=rules)
    assert matches["sample.txt"] == ["Dummy"]
