"""FastAPI application exposing scan submission and report retrieval endpoints."""

from __future__ import annotations

from fastapi import FastAPI

from orchestrator.worker import start_worker

from .routes import router

# FastAPI application
app = FastAPI(title="Rotterdam Scanner API")
app.include_router(router)

# Background worker to process scheduled jobs
start_worker()

__all__ = ["app"]
