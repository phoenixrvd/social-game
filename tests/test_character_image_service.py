from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import engine.updater.image_updater as image_updater_module
import engine.updater.updater as abstract_updater_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.updater.image_updater import ImageUpdater
from tests.fakes import FakeLogger


def _fake_npc(tmp_path: Path) -> Npc:
    img_path = tmp_path / "ref.png"
    img_path.write_bytes(b"ref")
    default_img_path = tmp_path / "default.png"
    default_img_path.write_bytes(b"default")
    scene_img_path = tmp_path / "scene.png"
    scene_img_path.write_bytes(b"scene")
    return Npc(
        npc_id="vika",
        description="desc",
        system_prompt="sys",
        state="state",
        ltm="ltm",
        scene=Scene(scene_id="default", description="scene", img=scene_img_path),
        img=default_img_path,
        img_current=img_path,
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
    refresh_prompt = tmp_path / "image_refresh.md"
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
    refresh_prompt.write_text(
        """refresh rules

Use identity.png only for face, hair, skin tone, body proportions, and anatomy.
If the prompt explicitly changes the character's age, adapt the person from identity.png to match that age while preserving the same core identity.

{{BASE_PROMPT}}""",
        encoding="utf-8",
    )
    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_build_prompt.md":
            return build_prompt.read_text(encoding="utf-8")
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_refresh.md":
            return refresh_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)

    updater = ImageUpdater()
    updater.emit_update()
    captured_prompt: dict[str, Any] = {"value": None}
    captured_render: dict[str, Any] = {"prompt": None, "current": None, "identity": None}

    def fake_optimizer(prompt: str) -> str:
        captured_prompt["value"] = prompt
        return "optimized prompt"

    monkeypatch.setattr(image_updater_module, "run_prompt", lambda prompt, model: fake_optimizer(prompt))
    def fake_refresh(prompt: str, current_img: bytes, identity_img: bytes | None = None) -> bytes:
        captured_render["prompt"] = prompt
        captured_render["current"] = current_img
        captured_render["identity"] = identity_img
        return b"generated"

    monkeypatch.setattr(image_updater_module, "refresh_img", fake_refresh)

    updater.schedule()

    generated_path = updater._image_path()
    prompt_path = updater._image_prompt_path()

    assert generated_path.read_bytes() == b"generated"
    assert prompt_path.read_text(encoding="utf-8") == "optimized prompt"
    assert captured_prompt["value"] is not None
    assert captured_render["prompt"] is not None
    assert "Use identity.png only for face, hair, skin tone, body proportions, and anatomy." in captured_render["prompt"]
    assert "If the prompt explicitly changes the character's age, adapt the person from identity.png to match that age while preserving the same core identity." in captured_render["prompt"]
    assert captured_render["prompt"].endswith("optimized prompt")
    assert captured_render["current"] == b"ref"
    assert captured_render["identity"] == b"default"
    assert "## Current Image Prompt\n(none)" in captured_prompt["value"]
    assert "## Current State\nstate" in captured_prompt["value"]
    assert "## Current Scene\nscene" in captured_prompt["value"]
    assert any(message.get("event") == "updater_active" and message.get("updater") == "image" and message.get("active") is True and message.get("prompt_start") is True for message in fake_logger.messages)
    assert {"event": "image_generation_prompt", "prompt": "optimized prompt"} in fake_logger.messages
    assert {"event": "image_generation_started", "source_image": tmp_path / "ref.png", "identity_image": tmp_path / "default.png", "target_image": generated_path} in fake_logger.messages
    assert {"event": "image_updated", "path": generated_path} in fake_logger.messages
    assert any(message.get("event") == "updater_completed" and message.get("updater") == "image" for message in fake_logger.messages)


def test_image_updater_schedule_skips_when_prompt_is_unchanged(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    build_prompt = tmp_path / "image_build_prompt.md"
    refresh_prompt = tmp_path / "image_refresh.md"
    build_prompt.write_text("build rules", encoding="utf-8")
    refresh_prompt.write_text("refresh {{BASE_PROMPT}}", encoding="utf-8")
    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_build_prompt.md":
            return build_prompt.read_text(encoding="utf-8")
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_refresh.md":
            return refresh_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)

    updater = ImageUpdater()
    updater.emit_update()
    updater._image_prompt_path().parent.mkdir(parents=True, exist_ok=True)
    updater._image_prompt_path().write_text("same prompt", encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "run_prompt", lambda _prompt, model: "same prompt")
    monkeypatch.setattr(
        image_updater_module,
        "refresh_img",
        lambda _prompt, _img, _identity=None: (_ for _ in ()).throw(AssertionError("Image generation must not run")),
    )

    updater.schedule()

    assert updater._image_path().exists() is False
    assert {"event": "image_skip", "reason": "prompt_unchanged_exact"} in fake_logger.messages


def test_image_updater_emit_update_if_missing_sets_trigger_when_runtime_image_is_missing(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()

    updater.emit_update_if_missing()

    assert updater._run_trigger_path().read_text(encoding="utf-8") == "1"


def test_image_updater_emit_update_if_missing_skips_when_runtime_image_exists(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()
    image_path = updater._image_path()
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"generated")

    updater.emit_update_if_missing()

    assert updater._run_trigger_path().exists() is False


def test_image_updater_revert_returns_noop_when_no_image_and_no_backup(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()

    result = updater.revert()

    assert result is None


def test_image_updater_revert_restores_backup_when_image_missing(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()
    image_path = updater._image_path()
    backup_dir = updater._backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "img-20260323-130000.png"
    backup.write_bytes(b"restored")

    result = updater.revert()

    assert result is None
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

    result = updater.revert()

    assert result is None
    assert image_path.read_bytes() == b"new"
    assert new_backup.exists() is False
    assert {"event": "image_revert_started", "target": image_path, "backup": new_backup} in fake_logger.messages
    assert {
        "event": "image_revert_completed",
        "revert": True,
        "target_image": image_path,
        "restored_from": new_backup,
    } in fake_logger.messages


def test_image_updater_refresh_image_with_current_prompt_persists_image(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    updater = ImageUpdater()
    image_path = updater._image_path()
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"old-image")

    updater._image_prompt_path().parent.mkdir(parents=True, exist_ok=True)
    updater._image_prompt_path().write_text("current prompt", encoding="utf-8")

    refresh_prompt = tmp_path / "image_refresh.md"
    refresh_prompt.write_text("refresh {{BASE_PROMPT}}", encoding="utf-8")

    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_refresh.md":
            return refresh_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)

    captured_render: dict[str, Any] = {"prompt": None, "current": None, "identity": None}

    def fake_refresh(prompt: str, current_img: bytes, identity_img: bytes | None = None) -> bytes:
        captured_render["prompt"] = prompt
        captured_render["current"] = current_img
        captured_render["identity"] = identity_img
        return b"new-image"

    monkeypatch.setattr(image_updater_module, "refresh_img", fake_refresh)

    result = updater.refresh_image_with_current_prompt()

    assert result is None
    assert image_path.read_bytes() == b"new-image"
    assert captured_render["prompt"] is not None
    assert captured_render["prompt"].endswith("current prompt")
    assert captured_render["current"] == b"ref"
    assert captured_render["identity"] == b"default"
    assert {"event": "image_refresh_started", "npc": "vika", "prompt_length": len("current prompt")} in fake_logger.messages
    assert {"event": "image_refreshed", "path": image_path, "image_bytes": len(b"new-image")} in fake_logger.messages


def test_image_updater_refresh_image_with_current_prompt_returns_noop_without_prompt(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()

    result = updater.refresh_image_with_current_prompt()

    assert result is None


def test_image_updater_refresh_image_with_current_prompt_propagates_refresh_errors(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    updater = ImageUpdater()
    updater._image_prompt_path().parent.mkdir(parents=True, exist_ok=True)
    updater._image_prompt_path().write_text("current prompt", encoding="utf-8")

    def failing_refresh(_prompt: str, _img: bytes, _identity: bytes | None = None) -> bytes:
        raise RuntimeError("moderation_blocked")

    monkeypatch.setattr(image_updater_module, "refresh_img", failing_refresh)

    try:
        updater.refresh_image_with_current_prompt()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        assert str(exc) == "moderation_blocked"

    assert updater._image_path().exists() is False
    assert {"event": "image_refresh_started", "npc": "vika", "prompt_length": len("current prompt")} in fake_logger.messages


def test_image_updater_merge_with_scene_persists_merged_image(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    scene_prompt = tmp_path / "image_scene.md"
    scene_prompt.write_text("merge {{SCENE_DESCRIPTION}}", encoding="utf-8")
    build_prompt = tmp_path / "image_build_prompt.md"
    build_prompt.write_text(
        """build\n{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}""",
        encoding="utf-8",
    )

    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_scene.md":
            return scene_prompt.read_text(encoding="utf-8")
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_build_prompt.md":
            return build_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)

    captured: dict[str, object] = {"update_prompt_source": None}

    def fake_merge(prompt: str, character_img_bytes: bytes, scene_img_bytes: bytes) -> bytes:
        captured["prompt"] = prompt
        captured["character_img_bytes"] = character_img_bytes
        captured["scene_img_bytes"] = scene_img_bytes
        return b"merged-image"

    monkeypatch.setattr(image_updater_module, "merge_character_scene_img", fake_merge)
    monkeypatch.setattr(
        image_updater_module,
        "run_prompt",
        lambda prompt, model: captured.__setitem__("update_prompt_source", prompt) or "initial update prompt",
    )

    updater = ImageUpdater()
    image_path = updater._image_path()
    prompt_path = updater._image_prompt_path()
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"old-image")

    result = updater.merge_with_scene()

    assert result is None
    assert captured["prompt"] == "merge scene"
    assert captured["character_img_bytes"] == b"ref"
    assert captured["scene_img_bytes"] == b"scene"
    assert captured["update_prompt_source"] == "build\n(none)\nstate\nscene"
    assert image_path.read_bytes() == b"merged-image"
    assert prompt_path.read_text(encoding="utf-8") == "initial update prompt"
    assert {"event": "image_merge_started", "source_image": tmp_path / "ref.png", "scene_image": tmp_path / "scene.png", "target_image": image_path} in fake_logger.messages
    assert {"event": "image_merged_with_scene", "path": image_path, "image_bytes": len(b"merged-image")} in fake_logger.messages


def test_image_updater_merge_with_scene_propagates_errors(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    scene_prompt = tmp_path / "image_scene.md"
    scene_prompt.write_text("merge {{SCENE_DESCRIPTION}}", encoding="utf-8")

    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_scene.md":
            return scene_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)

    def failing_merge(_prompt: str, _character_img_bytes: bytes, _scene_img_bytes: bytes) -> bytes:
        raise RuntimeError("merge_failed")

    monkeypatch.setattr(image_updater_module, "merge_character_scene_img", failing_merge)

    updater = ImageUpdater()

    try:
        updater.merge_with_scene()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        assert str(exc) == "merge_failed"

    assert updater._image_path().exists() is False


def test_image_updater_merge_with_scene_persists_initial_prompt_for_follow_up_schedule(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    scene_prompt = tmp_path / "image_scene.md"
    scene_prompt.write_text("merge {{SCENE_DESCRIPTION}}", encoding="utf-8")
    build_prompt = tmp_path / "image_build_prompt.md"
    build_prompt.write_text(
        """build\n{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}""",
        encoding="utf-8",
    )

    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_scene.md":
            return scene_prompt.read_text(encoding="utf-8")
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_build_prompt.md":
            return build_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)
    monkeypatch.setattr(image_updater_module, "merge_character_scene_img", lambda _prompt, _character, _scene: b"merged-image")
    monkeypatch.setattr(image_updater_module, "run_prompt", lambda _prompt, model: "stable update prompt")
    monkeypatch.setattr(
        image_updater_module,
        "refresh_img",
        lambda _prompt, _img, _identity=None: (_ for _ in ()).throw(AssertionError("refresh must not run without relevant change")),
    )

    updater = ImageUpdater()

    updater.merge_with_scene()
    assert updater._image_prompt_path().read_text(encoding="utf-8") == "stable update prompt"

    updater.emit_update()
    updater.schedule()

    assert updater._image_path().read_bytes() == b"merged-image"
    assert {"event": "image_skip", "reason": "prompt_unchanged_exact"} in fake_logger.messages


def test_image_updater_schedule_uses_initial_merge_when_runtime_image_is_missing(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    fake_logger = FakeLogger()
    monkeypatch.setattr(image_updater_module, "LOGGER", fake_logger)

    scene_prompt = tmp_path / "image_scene.md"
    scene_prompt.write_text("merge {{SCENE_DESCRIPTION}}", encoding="utf-8")
    build_prompt = tmp_path / "image_build_prompt.md"
    build_prompt.write_text(
        """build\n{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}""",
        encoding="utf-8",
    )

    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_scene.md":
            return scene_prompt.read_text(encoding="utf-8")
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_build_prompt.md":
            return build_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)

    captured: dict[str, object] = {"update_prompt_source": None}

    monkeypatch.setattr(
        image_updater_module,
        "run_prompt",
        lambda prompt, model: captured.__setitem__("update_prompt_source", prompt) or "initial update prompt",
    )

    def fake_merge(prompt: str, character_img_bytes: bytes, scene_img_bytes: bytes) -> bytes:
        captured["prompt"] = prompt
        captured["character_img_bytes"] = character_img_bytes
        captured["scene_img_bytes"] = scene_img_bytes
        return b"merged-image"

    monkeypatch.setattr(image_updater_module, "merge_character_scene_img", fake_merge)
    monkeypatch.setattr(
        image_updater_module,
        "refresh_img",
        lambda _prompt, _img, _identity=None: (_ for _ in ()).throw(AssertionError("refresh path must not run for initial image")),
    )

    updater = ImageUpdater()
    updater.emit_update()
    updater.schedule()

    assert updater._image_path().read_bytes() == b"merged-image"
    assert updater._image_prompt_path().read_text(encoding="utf-8") == "initial update prompt"
    assert captured["prompt"] == "merge scene"
    assert captured["character_img_bytes"] == b"ref"
    assert captured["scene_img_bytes"] == b"scene"
    assert captured["update_prompt_source"] == "build\n(none)\nstate\nscene"
    assert {"event": "image_merge_started", "source_image": tmp_path / "ref.png", "scene_image": tmp_path / "scene.png", "target_image": updater._image_path()} in fake_logger.messages
    assert {"event": "image_merged_with_scene", "path": updater._image_path(), "image_bytes": len(b"merged-image")} in fake_logger.messages


def test_image_updater_schedule_propagates_errors_without_exception_handling(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    build_prompt = tmp_path / "image_build_prompt.md"
    refresh_prompt = tmp_path / "image_refresh.md"
    build_prompt.write_text(
        """{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}""",
        encoding="utf-8",
    )
    refresh_prompt.write_text("refresh {{BASE_PROMPT}}", encoding="utf-8")
    def fake_load_text(path):
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_build_prompt.md":
            return build_prompt.read_text(encoding="utf-8")
        if path == image_updater_module.config.PROJECT_ROOT / "prompts" / "image_refresh.md":
            return refresh_prompt.read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")

    monkeypatch.setattr(image_updater_module, "load_text", fake_load_text)

    updater = ImageUpdater()

    prompts = iter(["first prompt", "second prompt"])
    monkeypatch.setattr(image_updater_module, "run_prompt", lambda _prompt, model: next(prompts))

    def failing_refresh(_prompt: str, _img: bytes, _identity: bytes | None = None) -> bytes:
        raise RuntimeError("moderation_blocked")

    monkeypatch.setattr(image_updater_module, "refresh_img", failing_refresh)

    updater.emit_update()
    try:
        updater.schedule()
    except RuntimeError:
        pass

    monkeypatch.setattr(image_updater_module, "refresh_img", lambda _prompt, _img, _identity=None: b"ok-image")
    updater.emit_update()
    updater.schedule()
