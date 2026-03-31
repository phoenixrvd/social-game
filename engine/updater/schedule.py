from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from engine.updater.ltm_updater import LtmUpdater
from engine.updater.scene_updater import SceneUpdater
from engine.updater.state_updater import StateUpdater
from engine.updater.image_updater import ImageUpdater
from engine.updater.updater import AbstractUpdater

UPDATER_CLASSES: tuple[tuple[str, type[AbstractUpdater]], ...] = (
    ("ltm", LtmUpdater),
    ("scene", SceneUpdater),
    ("state", StateUpdater),
    ("image", ImageUpdater),
)

AVAILABLE_UPDATERS = ", ".join(name for name, _cls in UPDATER_CLASSES)

def _add_job(scheduler: BackgroundScheduler, updater: AbstractUpdater) -> None:
    scheduler.add_job(
        updater.schedule,
        "interval",
        seconds=updater.get_update_interval(),
        max_instances=1,
        coalesce=True,
    )


def start_scheduler(
    *,
    scheduler: BackgroundScheduler | None = None,
    run_immediately: bool = True,
) -> tuple[BackgroundScheduler, list[AbstractUpdater]]:
    active_scheduler = scheduler or BackgroundScheduler()
    updaters = [cls() for _, cls in UPDATER_CLASSES]

    for updater in updaters:
        _add_job(active_scheduler, updater)
        if run_immediately:
            updater.schedule()

    active_scheduler.start()
    return active_scheduler, updaters


def stop_scheduler(scheduler: BackgroundScheduler | None) -> None:
    if scheduler is None:
        return
    scheduler.shutdown(wait=False)


