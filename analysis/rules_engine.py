"""Simple rule engine for evaluating analysis facts against YAML-defined rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

try:  # pragma: no cover - optional dependency
    import jmespath
except Exception:  # pragma: no cover - gracefully handle missing lib
    jmespath = None


@dataclass
class Rule:
    """Representation of a single rule loaded from YAML."""

    id: str
    severity: str
    selector: str
    remediation: str


def load_rules(rule_dir: Path) -> List[Rule]:
    """Load all rules from ``rule_dir``.

    Each YAML file may contain a top-level ``rules`` list or be a list itself.
    """
    rules: List[Rule] = []
    for path in rule_dir.glob("*.y*ml"):
        data = yaml.safe_load(path.read_text()) or {}
        items: Iterable[Dict[str, Any]]
        if isinstance(data, dict):
            items = data.get("rules", [])
        elif isinstance(data, list):
            items = data
        else:  # pragma: no cover - malformed yaml
            continue
        for item in items:
            try:
                rules.append(
                    Rule(
                        id=str(item.get("id", Path(path).stem)),
                        severity=str(item.get("severity", "info")),
                        selector=str(item.get("selector", "")),
                        remediation=str(item.get("remediation", "")),
                    )
                )
            except Exception:  # pragma: no cover - skip invalid entries
                continue
    return rules


def evaluate_rules(rules: List[Rule], facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluate ``rules`` against ``facts`` and return findings."""
    findings: List[Dict[str, Any]] = []
    for rule in rules:
        if not rule.selector:
            continue
        result: Any = None
        try:
            if jmespath is not None:
                result = jmespath.search(rule.selector, facts)
            else:  # pragma: no cover - jmespath missing
                result = facts.get(rule.selector)
        except Exception:  # pragma: no cover - selector errors
            continue
        if result:
            findings.append(
                {
                    "id": rule.id,
                    "severity": rule.severity,
                    "remediation": rule.remediation,
                    "matches": result,
                }
            )
    return findings
