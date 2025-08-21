from __future__ import annotations

"""Utilities for loading configuration files."""

from pathlib import Path
from typing import Any, Mapping, MutableMapping
import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - pass through
        raise ConfigError(f"Config file not found: {path}") from exc


def _parse(text: str, suffix: str) -> MutableMapping[str, Any]:
    if suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise ConfigError("PyYAML is required for YAML configuration files")
        data = yaml.safe_load(text) or {}
    elif suffix == ".json":
        data = json.loads(text or '{}')
    else:
        raise ConfigError(f"Unsupported config format: {suffix}")
    if not isinstance(data, MutableMapping):
        raise ConfigError("Configuration root must be a mapping")
    return data


def _validate(data: Mapping[str, Any], schema: Mapping[str, type] | None) -> None:
    if schema is None:
        return
    for key, typ in schema.items():
        if key not in data:
            raise ConfigError(f"Missing required key: {key}")
        if not isinstance(data[key], typ):
            raise ConfigError(
                f"Invalid type for '{key}': expected {typ.__name__}, got {type(data[key]).__name__}"
            )


def load(
    path: str | Path,
    schema: Mapping[str, type] | None = None,
    defaults: Mapping[str, Any] | None = None,
) -> MutableMapping[str, Any]:
    """Load a JSON or YAML configuration file and validate against ``schema``.

    ``defaults`` are merged with the loaded data (file values take precedence).
    """
    p = Path(path)
    text = _read_text(p)
    data = _parse(text, p.suffix.lower())
    if defaults:
        merged: MutableMapping[str, Any] = {**defaults, **data}
    else:
        merged = data
    _validate(merged, schema)
    return merged
