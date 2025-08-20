"""FastAPI application exposing scan submission and report retrieval endpoints."""

from __future__ import annotations

from fastapi import FastAPI

from orchestrator.worker import start_worker

from .routes import router
from .constants import APP_NAME, APP_VERSION

# FastAPI application
app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.include_router(router)

# Background worker to process scheduled jobs
start_worker()
