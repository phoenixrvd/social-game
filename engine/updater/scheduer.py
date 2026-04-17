from __future__ import annotations

import importlib
import pkgutil

from apscheduler.schedulers.background import BackgroundScheduler

from engine.updater import __path__ as updater_pkg_path
from engine.updater.updater import AbstractUpdater


class Scheduler:
    def __init__(self) -> None:
        self._scheduler: BackgroundScheduler | None = None

    def start(self) -> None:
        if self._scheduler is not None:
            return

        scheduler = BackgroundScheduler()

        for updater_cls in self._find_updater_classes():
            updater = updater_cls()
            scheduler.add_job(
                updater.schedule,
                "interval",
                seconds=updater.get_update_interval(),
                max_instances=1,
                coalesce=True,
            )
            updater.schedule()

        scheduler.start()
        self._scheduler = scheduler

    def stop(self) -> None:
        if self._scheduler is None:
            return

        self._scheduler.shutdown(wait=False)
        self._scheduler = None

    @staticmethod
    def create_updater(updater_name: str) -> AbstractUpdater:
        key = updater_name.strip().lower()
        return Scheduler._updater_classes()[key]()

    @staticmethod
    def available_updaters() -> str:
        return ", ".join(Scheduler._updater_classes())

    @staticmethod
    def _updater_classes() -> dict[str, type[AbstractUpdater]]:
        return {
            cls.__module__.rpartition(".")[2].removesuffix("_updater"): cls
            for cls in Scheduler._find_updater_classes()
        }

    @staticmethod
    def _find_updater_classes() -> list[type[AbstractUpdater]]:
        classes: list[type[AbstractUpdater]] = []

        for module_info in pkgutil.iter_modules(updater_pkg_path):
            module = importlib.import_module(f"engine.updater.{module_info.name}")
            classes.extend(
                value
                for value in vars(module).values()
                if isinstance(value, type)
                and issubclass(value, AbstractUpdater)
                and value is not AbstractUpdater
            )

        return classes
