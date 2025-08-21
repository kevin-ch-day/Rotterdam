from __future__ import annotations

from typing import Protocol

from .settings import Settings


class AuthPolicy(Protocol):
    def requires_auth(self, path: str, method: str) -> bool: ...


class SimpleApiPolicy:
    def __init__(self, settings: Settings):
        self.settings = settings

    def requires_auth(self, path: str, method: str) -> bool:
        if self.settings.disable_auth:
            return False
        return any(path.startswith(p) for p in self.settings.protect_prefixes)
