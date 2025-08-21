"""FastAPI application exposing scan submission and report retrieval endpoints."""

from __future__ import annotations

from fastapi import FastAPI

from app_config import app_config

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title=app_config.APP_NAME, version=app_config.APP_VERSION)
    app.include_router(router)
    return app
