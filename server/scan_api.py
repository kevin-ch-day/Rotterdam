"""FastAPI application exposing scan submission and report retrieval endpoints."""

from __future__ import annotations
from fastapi import FastAPI

from .routes import router
from .constants import APP_NAME, APP_VERSION

def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.include_router(router)
    return app
