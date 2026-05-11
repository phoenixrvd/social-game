from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path

from engine.storage.files import TextFile
from engine.storage.models import Message


@dataclass(frozen=True)
class _StmJsonlStore:
    path: Path

    def load(self) -> list[Message]:
        return [
            Message.model_validate(json.loads(line))
            for line in TextFile(self.path).get().splitlines()
            if line.strip()
        ]

    def save(self, messages: list[Message]) -> None:
        payload = "".join(json.dumps(msg.model_dump(), ensure_ascii=False) + "\n" for msg in messages)
        TextFile(self.path).save(payload)

    def append(self, message: Message) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(message.model_dump(), ensure_ascii=False) + "\n")

