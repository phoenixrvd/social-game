from __future__ import annotations

import json
import sqlite3

from dataclasses import dataclass
from pathlib import Path

from engine.storage.files import TextFile
from engine.storage.models import Episode, Message


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


@dataclass(frozen=True)
class _EtmSqliteStore:
    path: Path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS etm_entries (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
        return connection

    def append(self, id: str, text: str, embedding: list[float], created_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO etm_entries (id, text, embedding, created_at) VALUES (?, ?, ?, ?)",
                (id, text, json.dumps(embedding), created_at),
            )

    def delete(self, ids: list[str]) -> None:
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with self._connect() as connection:
            connection.execute(f"DELETE FROM etm_entries WHERE id IN ({placeholders})", ids)

    def get(self) -> list[Episode]:
        if not self.path.exists():
            return []
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, text, embedding, created_at FROM etm_entries"
            ).fetchall()
        return [
            Episode(
                id=str(id),
                text=str(text),
                embedding=[float(value) for value in json.loads(raw_embedding)],
                created_at=str(created_at),
            )
            for id, text, raw_embedding, created_at in rows
        ]

