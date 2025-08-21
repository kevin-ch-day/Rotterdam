from __future__ import annotations

import hmac
import os
from dataclasses import dataclass, replace
from typing import Iterable, Set, Tuple


class SettingsError(ValueError):
    """Raised when the application settings are misconfigured."""


from fastapi import Request

DEFAULT_API_KEY = "secret"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"{name} must be a boolean, got {raw!r}")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise SettingsError(f"{name} must be a positive integer, got {raw!r}")
    return value


@dataclass(frozen=True)
class Settings:
    api_keys: Set[str]
    default_api_key: str
    rate_limit: int
    rate_window_secs: int
    disable_auth: bool
    trust_localhost: bool
    trust_proxy: bool
    public_paths: Set[str]
    public_prefixes: Tuple[str, ...]
    protect_prefixes: Tuple[str, ...] = ("/api",)

    @classmethod
    def from_env(cls) -> "Settings":
        api_raw = os.getenv("ROTTERDAM_API_KEY", DEFAULT_API_KEY)
        api_keys = {k.strip() for k in api_raw.split(",") if k.strip()}
        rate_limit = _env_int("ROTTERDAM_RATE_LIMIT", 60)
        rate_window = _env_int("ROTTERDAM_RATE_WINDOW_SECS", 60)
        disable_auth = _env_bool("DISABLE_AUTH", True)
        trust_localhost = _env_bool("TRUST_LOCALHOST", False)
        trust_proxy = _env_bool("TRUST_PROXY", False)
        public_paths = {
            "/",
            "/_healthz",
            "/_ready",
            "/ui",
            "/static",
        }
        public_prefixes = (
            "/ui/",
            "/static/",
            "/css/",
            "/js/",
            "/images/",
            "/img/",
            "/fonts/",
            "/partials/",
        )
        protect_prefixes = ("/api",)
        return cls(
            api_keys=api_keys,
            default_api_key=DEFAULT_API_KEY,
            rate_limit=rate_limit,
            rate_window_secs=rate_window,
            disable_auth=disable_auth,
            trust_localhost=trust_localhost,
            trust_proxy=trust_proxy,
            public_paths=public_paths,
            public_prefixes=public_prefixes,
            protect_prefixes=protect_prefixes,
        )

    def __post_init__(self) -> None:
        if self.rate_limit <= 0:
            raise SettingsError("rate_limit must be positive")
        if self.rate_window_secs <= 0:
            raise SettingsError("rate_window_secs must be positive")

    def is_public(self, path: str) -> bool:
        return path in self.public_paths or any(path.startswith(p) for p in self.public_prefixes)

    def client_ip(self, request: Request) -> str:
        if self.trust_proxy:
            xff = request.headers.get("x-forwarded-for")
            if xff:
                return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def extract_api_key(self, request: Request) -> str | None:
        key = request.headers.get("X-API-Key")
        if key:
            return key.strip()
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip() or None
        return None

    def valid_api_key(self, presented: str) -> bool:
        result = 0
        for k in self.api_keys:
            result |= hmac.compare_digest(presented, k)
        return bool(result)
