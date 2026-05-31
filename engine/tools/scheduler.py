from __future__ import annotations

import time

from apscheduler.schedulers.background import BackgroundScheduler

from engine.logger import logger
from engine.tools.abstract_job import AbstractJob
from engine.tools.etm_job import EtmJob
from engine.tools.image_job import ImageJob
from engine.tools.scene_job import SceneJob
from engine.tools.state_job import StateJob

_scheduler_instance: Scheduler | None = None


class Scheduler:
    def __init__(self) -> None:
        self._scheduler: BackgroundScheduler | None = None
        self._jobs: dict[str, AbstractJob] = {
            "etm": EtmJob(),
            "state": StateJob(),
            "scene": SceneJob(),
            "image": ImageJob(),
        }
        self._pending_jobs: set[str] = set()
        self._last_execution_time: dict[str, float] = {}

    def enqueue(self, job_name: str) -> None:
        if job_name not in self._jobs or job_name in self._pending_jobs:
            return

        self._pending_jobs.add(job_name)
        logger.info("Job in Warteschlange: %s", job_name)

    def enqueue_all(self) -> None:
        for job_name in self._jobs:
            self.enqueue(job_name)

    def clear_pending_jobs(self) -> None:
        self._pending_jobs.clear()

    def execute_pending_jobs(self) -> None:
        now = time.time()

        for job_name, job in self._jobs.items():
            if job_name not in self._pending_jobs:
                continue

            last_run_at = self._last_execution_time.get(job_name, 0)
            if now - last_run_at < job.rate_limit_seconds:
                continue

            logger.info("Job wird gestartet: %s", job_name)
            self._last_execution_time[job_name] = now
            job.execute()
            logger.info("Job wurde ausgeführt: %s", job_name)

            self._pending_jobs.remove(job_name)

    def start(self) -> None:
        if self._scheduler is not None:
            return

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self.execute_pending_jobs,
            "interval",
            seconds=10,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()

    def stop(self) -> None:
        if self._scheduler is None:
            return

        self._scheduler.shutdown(wait=False)
        self._scheduler = None


def set_scheduler(scheduler: Scheduler) -> None:
    global _scheduler_instance
    _scheduler_instance = scheduler


def get_scheduler() -> Scheduler:
    if _scheduler_instance is None:
        raise RuntimeError("Scheduler ist nicht initialisiert.")
    return _scheduler_instance
