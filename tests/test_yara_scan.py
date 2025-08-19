import pytest
import pytest
from pathlib import Path

from analysis.yara_scan import compile_rules, scan_directory


try:  # Skip if libyara is missing
    yara = pytest.importorskip("yara")
except OSError:  # pragma: no cover - environment dependent
    pytest.skip("libyara not available", allow_module_level=True)


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
