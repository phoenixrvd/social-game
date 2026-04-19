from __future__ import annotations

import logging

import engine.tools.scheduler as scheduler_module
from engine.tools.abstract_job import AbstractJob


class DemoJob(AbstractJob):
    rate_limit_seconds = 0

    def __init__(self) -> None:
        self.run_count = 0

    def execute(self) -> None:
        self.run_count += 1


def test_enqueue_logs_activation(caplog):
    caplog.set_level(logging.INFO)
    scheduler = scheduler_module.Scheduler()

    scheduler.enqueue("etm")

    assert "Job in Warteschlange: etm" in caplog.text
    assert scheduler._pending_jobs == {"etm"}


def test_execute_pending_jobs_logs_execution(caplog):
    caplog.set_level(logging.INFO)
    scheduler = scheduler_module.Scheduler()
    scheduler.enqueue("etm")
    caplog.clear()

    scheduler.execute_pending_jobs()

    assert "Job wird gestartet: etm" in caplog.text
    assert "Job wurde ausgeführt: etm" in caplog.text
    assert not scheduler._pending_jobs


def test_enqueue_all_marks_every_job_pending():
    scheduler = scheduler_module.Scheduler()

    scheduler.enqueue_all()

    assert scheduler._pending_jobs == {"etm", "state", "scene", "image"}


def test_clear_pending_jobs_removes_all_pending_entries():
    scheduler = scheduler_module.Scheduler()
    scheduler.enqueue_all()

    scheduler.clear_pending_jobs()

    assert scheduler._pending_jobs == set()


def test_start_registers_execute_pending_jobs_job():
    captured: dict[str, object] = {}

    class FakeBackgroundScheduler:
        def add_job(self, func, trigger, **kwargs):
            captured["func"] = func
            captured["trigger"] = trigger
            captured["kwargs"] = kwargs

        def start(self) -> None:
            captured["started"] = True

    import unittest.mock
    with unittest.mock.patch.object(scheduler_module, "BackgroundScheduler", FakeBackgroundScheduler):
        scheduler = scheduler_module.Scheduler()
        scheduler.start()

        assert captured["func"] == scheduler.execute_pending_jobs
        assert captured["trigger"] == "interval"
        assert captured["kwargs"] == {"seconds": 10, "max_instances": 1, "coalesce": True}
        assert captured["started"] is True
