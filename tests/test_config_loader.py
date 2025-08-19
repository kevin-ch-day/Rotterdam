import pytest

from config.loader import load, ConfigError
from core.config import GlobalConfig


def test_load_with_schema_and_defaults(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"a": 1}')
    data = load(cfg, schema={"a": int, "b": str}, defaults={"b": "x"})
    assert data["a"] == 1
    assert data["b"] == "x"


def test_load_missing_key_raises(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"a": 1}')
    with pytest.raises(ConfigError):
        load(cfg, schema={"a": int, "b": int})


def test_global_config_load(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"port": 42}')
    gc = GlobalConfig()
    gc.load(cfg, schema={"port": int})
    assert gc["port"] == 42


def test_global_config_defaults(tmp_path):
    gc = GlobalConfig()
    gc.load(tmp_path / "missing.json", defaults={"debug": True})
    assert gc["debug"] is True
