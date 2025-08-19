"""Ensure completed jobs are pruned after TTL."""

from __future__ import annotations

import time

from workers.scheduler import Scheduler


def test_prune_jobs_removes_old_entries():
    sched = Scheduler()
    job_id = sched.submit_job(lambda: None)
    job = sched.get_job(job_id)
    assert job is not None
    # Make job appear old
    job.created_at -= 7200
    sched.mark_done(job, None)
    # Should prune immediately since job is older than default TTL
    assert sched.get_job(job_id) is None
