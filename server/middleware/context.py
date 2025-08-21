from __future__ import annotations

import contextvars

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def set_request_id(req_id: str) -> None:
    _request_id_ctx.set(req_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()
