from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractJob(ABC):
    rate_limit_seconds: int

    @abstractmethod
    def execute(self) -> None:
        pass

