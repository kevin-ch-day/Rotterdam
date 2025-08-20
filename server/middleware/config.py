from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MiddlewareSettings:
    """Configuration values loaded from environment variables."""

    default_api_key: str = "secret"
    api_keys: set[str] = field(default_factory=set)
    rate_limit: int = 60
    rate_window_secs: int = 60
    disable_auth: bool = False
    trust_localhost: bool = False
    trust_proxy: bool = False
    public_paths: set[str] = field(default_factory=set)
    public_prefixes: tuple[str, ...] = ()

    @staticmethod
    def _env_bool(name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _env_int(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None or not raw.strip():
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    @classmethod
    def from_env(cls) -> "MiddlewareSettings":
        default_api_key = "secret"
        api_keys_env = os.getenv("ROTTERDAM_API_KEY", default_api_key)
        api_keys = {k.strip() for k in api_keys_env.split(",") if k.strip()}

        rate_limit = max(1, cls._env_int("ROTTERDAM_RATE_LIMIT", 60))
        rate_window_secs = max(1, cls._env_int("ROTTERDAM_RATE_WINDOW_SECS", 60))

        disable_auth = cls._env_bool("DISABLE_AUTH", False)
        trust_localhost = cls._env_bool("TRUST_LOCALHOST", False)
        trust_proxy = cls._env_bool("TRUST_PROXY", False)

        public_paths = {
            "/",
            "/favicon.ico",
            "/_healthz",
            "/_ready",
            "/ui",
            "/static",
            "/css",
            "/js",
            "/images",
            "/img",
            "/fonts",
        }
        public_prefixes = (
            "/ui/",
            "/static/",
            "/css/",
            "/js/",
            "/images/",
            "/img/",
            "/fonts/",
        )

        if default_api_key in api_keys and not disable_auth:
            logging.getLogger("uvicorn.error").critical(
                "ROTTERDAM_API_KEY is using the default value; set a custom key for production",
            )

        return cls(
            default_api_key=default_api_key,
            api_keys=api_keys,
            rate_limit=rate_limit,
            rate_window_secs=rate_window_secs,
            disable_auth=disable_auth,
            trust_localhost=trust_localhost,
            trust_proxy=trust_proxy,
            public_paths=public_paths,
            public_prefixes=public_prefixes,
        )


settings = MiddlewareSettings.from_env()

# Backwards-compatible module-level constants
DEFAULT_API_KEY = settings.default_api_key
API_KEYS = settings.api_keys
RATE_LIMIT = settings.rate_limit
RATE_WINDOW_SECS = settings.rate_window_secs
DISABLE_AUTH = settings.disable_auth
TRUST_LOCALHOST = settings.trust_localhost
TRUST_PROXY = settings.trust_proxy
PUBLIC_PATHS = settings.public_paths
PUBLIC_PREFIXES = settings.public_prefixes

__all__ = [
    "MiddlewareSettings",
    "settings",
    "DEFAULT_API_KEY",
    "API_KEYS",
    "RATE_LIMIT",
    "RATE_WINDOW_SECS",
    "DISABLE_AUTH",
    "TRUST_LOCALHOST",
    "TRUST_PROXY",
    "PUBLIC_PATHS",
    "PUBLIC_PREFIXES",
]

