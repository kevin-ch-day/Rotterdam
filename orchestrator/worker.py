"""Worker routines for processing queued jobs."""
from __future__ import annotations

from typing import Any

from .scheduler import scheduler, Job


def worker_loop() -> None:
    """Continuously pull jobs from the scheduler and execute them."""
    while True:
        job: Job = scheduler.get_next_job()
        try:
            scheduler.mark_running(job)
            result = job.func(*job.args, **job.kwargs)
            scheduler.mark_done(job, result)
        except Exception as exc:  # pragma: no cover - simple error capture
            scheduler.mark_failed(job, exc)


def start_worker(daemon: bool = True) -> None:
    """Start a background thread running :func:`worker_loop`."""
    import threading

    thread = threading.Thread(target=worker_loop, daemon=daemon)
    thread.start()
    return thread
