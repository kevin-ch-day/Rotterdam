import json
from pathlib import Path

from analysis.diff import diff_snapshots


def test_diff_snapshots(tmp_path: Path) -> None:
    old = tmp_path / "v1.json"
    new = tmp_path / "v2.json"
    old.write_text(
        json.dumps({"permissions": ["a", "b"], "components": {"activity": ["Main"]}})
    )
    new.write_text(
        json.dumps(
            {
                "permissions": ["b", "c"],
                "components": {"activity": ["Main", "Second"], "service": ["Svc"]},
            }
        )
    )
    diff = diff_snapshots(old, new)
    assert diff["added_permissions"] == ["c"]
    assert diff["removed_permissions"] == ["a"]
    assert diff["added_components"]["activity"] == ["Second"]
    assert diff["added_components"]["service"] == ["Svc"]
    assert diff["removed_components"] == {}
