import pytest
from pathlib import Path

from analysis.yara_scan import compile_rules, scan_directory

# The yara Python bindings sometimes fail to load if the underlying
# native library is missing or incompatible with the runtime. Instead
# of erroring during collection, skip the test when yara cannot be
# imported for any reason.
try:  # pragma: no cover - import guarded for test environment
    import yara  # type: ignore
except Exception:  # noqa: BLE001 - broad to catch OSError/AttributeError
    pytest.skip("yara library unavailable", allow_module_level=True)


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
