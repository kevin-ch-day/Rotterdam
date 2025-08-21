"""In-memory job queue utilities.

This consolidates the previous `workers` and `orchestrator` packages into a
single module providing a scheduler and helper to start background workers.
"""
from __future__ import annotations

import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Job:
    """Represents a unit of work to be processed."""

    id: str
    func: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    status: str = "queued"
    result: Any | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class Scheduler:
    """Basic scheduler backed by :class:`queue.Queue`."""

    def __init__(self) -> None:
        self._queue: queue.Queue[Job] = queue.Queue()
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit_job(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """Queue a new job and return its identifier."""
        job_id = uuid.uuid4().hex
        job = Job(job_id, func, args, kwargs)
        with self._lock:
            self._jobs[job_id] = job
        self._queue.put(job)
        return job_id

    def get_next_job(self, timeout: float | None = None) -> Job:
        """Return the next job from the queue, blocking if necessary."""
        return self._queue.get(timeout=timeout)

    def mark_running(self, job: Job) -> None:
        """Mark a job as running."""
        with self._lock:
            job.status = "running"

    def mark_done(self, job: Job, result: Any) -> None:
        """Record successful completion of a job."""
        with self._lock:
            job.status = "completed"
            job.result = result
        self._queue.task_done()
        self.prune_jobs()

    def mark_failed(self, job: Job, exc: Exception) -> None:
        """Record a job failure."""
        with self._lock:
            job.status = "failed"
            job.error = str(exc)
        self._queue.task_done()
        self.prune_jobs()

    def job_status(self, job_id: str) -> str:
        """Return the status for ``job_id``."""
        with self._lock:
            job = self._jobs.get(job_id)
            return job.status if job else "unknown"

    def get_job(self, job_id: str) -> Job | None:
        """Return the :class:`Job` instance for ``job_id`` if known."""
        with self._lock:
            return self._jobs.get(job_id)

    def job_result(self, job_id: str) -> Any | None:
        """Return the result stored for ``job_id`` if completed."""
        job = self.get_job(job_id)
        return job.result if job else None

    def job_error(self, job_id: str) -> str | None:
        """Return the error message for ``job_id`` if it failed."""
        job = self.get_job(job_id)
        return job.error if job else None

    def list_jobs(self) -> dict[str, str]:
        """Return mapping of job IDs to their statuses."""
        with self._lock:
            return {job_id: job.status for job_id, job in self._jobs.items()}

    def prune_jobs(self, ttl: float = 3600.0) -> None:
        """Remove completed/failed jobs older than ``ttl`` seconds."""
        cutoff = time.time() - ttl
        with self._lock:
            to_delete = [
                job_id
                for job_id, job in self._jobs.items()
                if job.status in {"completed", "failed"} and job.created_at < cutoff
            ]
            for job_id in to_delete:
                del self._jobs[job_id]

    def wait_for_all(self) -> None:
        """Block until all queued jobs are processed."""
        self._queue.join()


scheduler = Scheduler()


def worker_loop() -> None:
    """Continuously pull jobs from the scheduler and execute them."""
    while True:
        job = scheduler.get_next_job()
        try:
            scheduler.mark_running(job)
            result = job.func(*job.args, **job.kwargs)
            scheduler.mark_done(job, result)
        except Exception as exc:  # pragma: no cover - simple error capture
            scheduler.mark_failed(job, exc)


def start_worker(daemon: bool = True) -> threading.Thread:
    """Start a background thread running :func:`worker_loop`."""
    thread = threading.Thread(target=worker_loop, daemon=daemon)
    thread.start()
    return thread
