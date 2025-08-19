"""Worker routines for processing queued jobs."""
from __future__ import annotations

from typing import Any

from .scheduler import Job
from orchestrator import scheduler as scheduler_module


def worker_loop() -> None:
    """Continuously pull jobs from the scheduler and execute them."""
    while True:
        sched = scheduler_module.scheduler
        job: Job = sched.get_next_job()
        try:
            sched.mark_running(job)
            result = job.func(*job.args, **job.kwargs)
            sched.mark_done(job, result)
        except Exception as exc:  # pragma: no cover - simple error capture
            sched.mark_failed(job, exc)


def start_worker(daemon: bool = True) -> None:
    """Start a background thread running :func:`worker_loop`."""
    import threading

    thread = threading.Thread(target=worker_loop, daemon=daemon)
    thread.start()
    return thread
