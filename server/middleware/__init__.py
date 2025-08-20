from . import auth_rate_limit as _auth
from . import request_id as _request
from .config import (
    DEFAULT_API_KEY,
    API_KEYS,
    RATE_LIMIT,
    RATE_WINDOW_SECS,
    DISABLE_AUTH,
    TRUST_LOCALHOST,
    TRUST_PROXY,
    PUBLIC_PATHS,
    PUBLIC_PREFIXES,
    MiddlewareSettings,
    settings,
)

AuthRateLimitMiddleware = _auth.AuthRateLimitMiddleware
RequestIDMiddleware = _request.RequestIDMiddleware
get_request_id = _request.get_request_id
_request_log = _auth._request_log
_cleanup_request_log = _auth._cleanup_request_log

__all__ = [
    "AuthRateLimitMiddleware",
    "RequestIDMiddleware",
    "get_request_id",
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
    "_request_log",
    "_cleanup_request_log",
    "_last_cleanup",
]

import sys
import types


class _MiddlewareModule(types.ModuleType):
    def __getattr__(self, name: str):
        if name == "_last_cleanup":
            return _auth._last_cleanup
        return super().__getattr__(name)

    def __setattr__(self, name: str, value):
        if name == "_last_cleanup":
            _auth._last_cleanup = value
        else:
            super().__setattr__(name, value)


sys.modules[__name__].__class__ = _MiddlewareModule
