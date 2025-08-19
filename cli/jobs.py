"""Command-line helpers for job queue interaction."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from analysis import analyze_apk
from orchestrator import scheduler, start_worker


def submit(apk: str) -> str:
    """Submit an APK for analysis and return the job ID."""
    path = Path(apk)
    if not path.exists():
        raise FileNotFoundError(f"{apk} does not exist")
    job_id = scheduler.submit_job(analyze_apk, str(path))
    print(f"Job submitted: {job_id}")
    return job_id


def status(job_id: Optional[str] = None) -> None:
    """Print the status of a single job or all jobs."""
    if job_id:
        print(f"{job_id}: {scheduler.job_status(job_id)}")
        return
    for jid, stat in scheduler.list_jobs().items():
        print(f"{jid}: {stat}")


def result(job_id: str) -> None:
    """Print the stored result or error for ``job_id``."""
    job = scheduler.get_job(job_id)
    if not job:
        print(f"{job_id}: unknown")
        return
    if job.status == "completed":
        print(job.result)
    elif job.status == "failed":
        print(job.error)
    else:
        print(f"{job_id}: {job.status}")


def main(argv: list[str] | None = None) -> None:
    """Entry point for job queue commands."""
    parser = argparse.ArgumentParser(description="Job queue utilities")
    sub = parser.add_subparsers(dest="cmd")

    p_submit = sub.add_parser("submit", help="submit APK for analysis")
    p_submit.add_argument("apk")

    p_status = sub.add_parser("status", help="show job status")
    p_status.add_argument("job_id", nargs="?", default=None)

    p_result = sub.add_parser("result", help="show job result or error")
    p_result.add_argument("job_id")

    sub.add_parser("worker", help="start a worker and process jobs")

    args = parser.parse_args(argv)
    if args.cmd == "submit":
        submit(args.apk)
    elif args.cmd == "status":
        status(args.job_id)
    elif args.cmd == "result":
        result(args.job_id)
    elif args.cmd == "worker":
        # Start worker in foreground and wait for queue to empty
        start_worker(daemon=False)
        scheduler.wait_for_all()
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
