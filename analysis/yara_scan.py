"""Helpers for scanning files with YARA rules."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from core import display

try:
    import yara  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yara = None


def compile_rules(rule_dir: Path) -> "yara.Rules":
    """Compile all ``*.yar`` files in ``rule_dir``.

    Raises ``RuntimeError`` if ``yara-python`` is unavailable or no rules are
    found.  Rule file stems are used as namespace identifiers.
    """

    if yara is None:
        raise RuntimeError("yara-python is not installed")

    files = {p.stem: str(p) for p in rule_dir.glob("*.yar") if p.is_file()}
    if not files:
        raise RuntimeError(f"No YARA rules found in {rule_dir}")
    return yara.compile(filepaths=files)


def scan_directory(
    target: Path, *, rule_dir: Path | None = None, rules: "yara.Rules" | None = None
) -> Dict[str, List[str]]:
    """Scan ``target`` directory with YARA rules.

    ``rule_dir`` points to a directory containing ``*.yar`` files.  If ``rules``
    is provided, it will be used directly.  Returns a mapping of relative file
    paths to lists of matching rule names.
    """

    if yara is None:
        raise RuntimeError("yara-python is not installed")

    if rules is None:
        rules = compile_rules(rule_dir or Path("rules/android"))

    matches: Dict[str, List[str]] = {}
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        try:
            res = rules.match(str(path))
        except Exception as exc:  # pragma: no cover - defensive
            display.warn(f"yara scan failed for {path}: {exc}")
            continue
        if res:
            matches[str(path.relative_to(target))] = [m.rule for m in res]
    return matches
