from __future__ import annotations

import yaml

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class StorageFile(ABC):
    path: Path

    @abstractmethod
    def get(self) -> Any:
        ...

    @abstractmethod
    def save(self, value: Any) -> None:
        ...

    def is_file(self) -> bool:
        return self.path.is_file()

    def exists(self) -> bool:
        return self.path.exists()

    @property
    def name(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class TextFile(StorageFile):
    def get(self) -> str:
        return self.path.read_text(encoding="utf-8") if self.path.exists() else ""

    def save(self, value: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(value, encoding="utf-8")


@dataclass(frozen=True)
class YamlFile(StorageFile):
    def get(self) -> dict[str, Any]:
        return yaml.safe_load(TextFile(self.path).get()) or {}

    def save(self, value: dict[str, Any]) -> None:
        TextFile(self.path).save(yaml.safe_dump(value, allow_unicode=True, sort_keys=False))


@dataclass(frozen=True)
class ImageFile(StorageFile):
    def get(self) -> Path:
        return self.path

    def save(self, value: bytes) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(value)


