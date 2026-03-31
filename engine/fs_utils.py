import json
from pathlib import Path
from typing import Any
import yaml


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(load_text(path)) or {}


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    save_text(path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in load_text(path).splitlines()
        if line.strip()
    ]


def save_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    save_text(path, "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows))


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    existing = load_text(path)
    new_line = json.dumps(data, ensure_ascii=True) + "\n"
    save_text(path, existing + new_line)
