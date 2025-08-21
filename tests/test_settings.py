from server import serv_config as legacy
from settings import get_settings


def clear_cache():
    get_settings.cache_clear()  # type: ignore[attr-defined]


def test_defaults(monkeypatch):
    monkeypatch.delenv("APP_HOST", raising=False)
    monkeypatch.delenv("APP_PORT", raising=False)
    monkeypatch.delenv("UVICORN_LOG_LEVEL", raising=False)
    monkeypatch.delenv("OPEN_BROWSER", raising=False)
    clear_cache()
    s = get_settings()
    assert s.host == legacy.DEFAULT_HOST
    assert s.port == legacy.DEFAULT_PORT
    assert s.log_level == legacy.DEFAULT_LOG_LEVEL
    assert s.open_browser is True


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("APP_HOST", "0.0.0.0")
    monkeypatch.setenv("APP_PORT", "9999")
    monkeypatch.setenv("UVICORN_LOG_LEVEL", "debug")
    monkeypatch.setenv("OPEN_BROWSER", "false")
    clear_cache()
    s = get_settings()
    assert s.host == "0.0.0.0"
    assert s.port == 9999
    assert s.log_level == "debug"
    assert s.open_browser is False
