import pytest
from starlette.applications import Starlette

from server.middleware.auth_rate_limit import AuthRateLimitMiddleware
from server.middleware.settings import Settings, SettingsError


def test_invalid_rate_limit(monkeypatch):
    monkeypatch.setenv("ROTTERDAM_RATE_LIMIT", "abc")
    with pytest.raises(SettingsError):
        Settings.from_env()


def test_invalid_disable_auth(monkeypatch):
    monkeypatch.setenv("DISABLE_AUTH", "maybe")
    with pytest.raises(SettingsError):
        Settings.from_env()


def test_middleware_requires_api_keys(monkeypatch):
    monkeypatch.setenv("DISABLE_AUTH", "0")
    monkeypatch.setenv("ROTTERDAM_API_KEY", "")
    app = Starlette()
    with pytest.raises(SettingsError):
        AuthRateLimitMiddleware(app)
