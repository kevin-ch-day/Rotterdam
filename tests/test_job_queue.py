from orchestrator.scheduler import Scheduler
import orchestrator.scheduler as scheduler_module
import orchestrator.worker as worker_module
import cli.jobs as jobs


def _reset_scheduler():
    sched = Scheduler()
    scheduler_module.scheduler = sched
    worker_module.scheduler = sched
    jobs.scheduler = sched
    return sched


def test_job_lifecycle(tmp_path, monkeypatch, capsys):
    sched = _reset_scheduler()
    monkeypatch.setattr(jobs, "analyze_apk", lambda path: "ok")

    apk = tmp_path / "dummy.apk"
    apk.write_text("data")

    job_id = jobs.submit(str(apk))
    worker_module.start_worker(daemon=True)
    sched.wait_for_all()

    jobs.status(job_id)
    assert "completed" in capsys.readouterr().out

    jobs.result(job_id)
    assert capsys.readouterr().out.strip() == "ok"
