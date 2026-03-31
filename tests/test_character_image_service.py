from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import engine.updater.image_updater as image_updater_module
import engine.updater.updater as abstract_updater_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.updater.image_updater import ImageUpdater


class FakeLogger:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def info(self, message: object, *args) -> None:
        if isinstance(message, str) and args:
            self.messages.append(message % args)
            return

        self.messages.append(message)


def _fake_npc(tmp_path: Path) -> Npc:
    img_path = tmp_path / "ref.png"
    img_path.write_bytes(b"ref")
    return Npc(
        npc_id="vika",
        description="desc",
        system_prompt="sys",
        state="state",
        ltm="ltm",
        scene=Scene(scene_id="default", description="scene"),
        img=img_path,
        stm=[
            ShortMemoryMessage(
                id="1",
                timestamp_utc=datetime.now(UTC).isoformat(),
                role="user",
                content="hi",
            )
        ],
        character={"name": "vika"},
    )


def _patch_stores(monkeypatch, tmp_path: Path) -> None:
    class FakeNpcStore:
        def load(self):
            return _fake_npc(tmp_path)

    monkeypatch.setattr(image_updater_module, "NpcStore", FakeNpcStore)
    monkeypatch.setattr(abstract_updater_module.config, "DATA_NPC_DIR", tmp_path / "npcs")


def test_image_updater_schedule_generates_image_and_persists_prompt(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    build_prompt = tmp_path / "image_build_prompt.md"
    build_prompt.write_text(
        """build rules

## Current Image Prompt
{{CURRENT_IMAGE_PROMPT}}

## Current State
{{CURRENT_STATE}}

## Current Scene
{{CURRENT_SCENE}}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(image_updater_module, "BUILD_IMAGE_PROMPT_PATH", build_prompt)

    updater = ImageUpdater()
    updater.emit_update()
    captured_prompt: dict[str, Any] = {"value": None}

    def fake_optimizer(prompt: str) -> str:
        captured_prompt["value"] = prompt
        return "optimized prompt"

    monkeypatch.setattr(image_updater_module, "run_prompt_small", fake_optimizer)
    monkeypatch.setattr(image_updater_module, "refresh_img", lambda _prompt, _img: b"generated")

    updater.schedule()

    generated_path = updater._image_path()
    prompt_path = updater._image_prompt_path()

    assert generated_path.read_bytes() == b"generated"
    assert prompt_path.read_text(encoding="utf-8") == "optimized prompt"
    assert captured_prompt["value"] is not None
    assert "## Current Image Prompt\n(none)" in captured_prompt["value"]
    assert "## Current State\nstate" in captured_prompt["value"]
    assert "## Current Scene\nscene" in captured_prompt["value"]
    assert any(message.get("event") == "updater_active" and message.get("updater") == "image" and message.get("active") is True and message.get("prompt_start") is True for message in fake_logger.messages)
    assert {"event": "image_generation_prompt", "prompt": "optimized prompt"} in fake_logger.messages
    assert {"event": "image_generation_started", "source_image": tmp_path / "ref.png", "target_image": generated_path} in fake_logger.messages
    assert {"event": "image_updated", "path": generated_path} in fake_logger.messages
    assert any(message.get("event") == "updater_completed" and message.get("updater") == "image" for message in fake_logger.messages)


def test_image_updater_schedule_skips_when_prompt_is_unchanged(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    build_prompt = tmp_path / "image_build_prompt.md"
    build_prompt.write_text("build rules", encoding="utf-8")
    monkeypatch.setattr(image_updater_module, "BUILD_IMAGE_PROMPT_PATH", build_prompt)

    updater = ImageUpdater()
    updater.emit_update()
    updater._image_prompt_path().parent.mkdir(parents=True, exist_ok=True)
    updater._image_prompt_path().write_text("same prompt", encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "run_prompt_small", lambda _prompt: "same prompt")
    monkeypatch.setattr(
        image_updater_module,
        "refresh_img",
        lambda _prompt, _img: (_ for _ in ()).throw(AssertionError("Image generation must not run")),
    )

    updater.schedule()

    assert updater._image_path().exists() is False
    assert {"event": "image_skip", "reason": "prompt_unchanged_exact"} in fake_logger.messages


def test_image_updater_revert_returns_noop_when_no_image_and_no_backup(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()

    output, did_revert = updater.revert()

    assert did_revert is False
    assert output == "Kein Daten-Bild vorhanden fuer 'vika'."


def test_image_updater_revert_restores_backup_when_image_missing(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()
    image_path = updater._image_path()
    backup_dir = updater._backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "img-20260323-130000.png"
    backup.write_bytes(b"restored")

    output, did_revert = updater.revert()

    assert did_revert is True
    assert "Bild geloescht." not in output
    assert f"Backup wiederhergestellt: {backup} -> {image_path}" in output
    assert image_path.read_bytes() == b"restored"
    assert backup.exists() is False


def test_image_updater_revert_deletes_image_and_restores_latest_backup(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    updater = ImageUpdater()
    image_path = updater._image_path()
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"current")

    backup_dir = updater._backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)
    old_backup = backup_dir / "img-20260323-120000.png"
    new_backup = backup_dir / "img-20260323-130000.png"
    old_backup.write_bytes(b"old")
    new_backup.write_bytes(b"new")

    output, did_revert = updater.revert()

    assert did_revert is True
    assert "Bild geloescht." in output
    assert f"Backup wiederhergestellt: {new_backup} -> {image_path}" in output
    assert image_path.read_bytes() == b"new"
    assert new_backup.exists() is False
    assert {"event": "image_revert_started", "target": image_path, "backup": new_backup} in fake_logger.messages
    assert {
        "event": "image_revert_completed",
        "revert": True,
        "target_image": image_path,
        "restored_from": new_backup,
    } in fake_logger.messages


def test_image_updater_persists_last_error_and_clears_it_after_success(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    build_prompt = tmp_path / "image_build_prompt.md"
    build_prompt.write_text(
        """{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}""",
        encoding="utf-8",
    )
    monkeypatch.setattr(image_updater_module, "BUILD_IMAGE_PROMPT_PATH", build_prompt)

    updater = ImageUpdater()

    prompts = iter(["first prompt", "second prompt"])
    monkeypatch.setattr(image_updater_module, "run_prompt_small", lambda _prompt: next(prompts))

    def failing_refresh(_prompt: str, _img: bytes) -> bytes:
        raise RuntimeError("moderation_blocked")

    monkeypatch.setattr(image_updater_module, "refresh_img", failing_refresh)

    updater.emit_update()
    try:
        updater.schedule()
    except RuntimeError:
        pass

    assert updater.get_last_error() == "moderation_blocked"

    monkeypatch.setattr(image_updater_module, "refresh_img", lambda _prompt, _img: b"ok-image")
    updater.emit_update()
    updater.schedule()

    assert updater.get_last_error() == ""

