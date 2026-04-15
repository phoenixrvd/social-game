from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import engine.services.character_image_service as character_image_service_module
import engine.storage as storage_module
from engine.models import Npc, Scene, ShortMemoryMessage
from engine.updater.image_updater import ImageUpdater


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
        relationship="relationship",
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

    monkeypatch.setattr(character_image_service_module, "NpcStore", FakeNpcStore)
    monkeypatch.setattr(storage_module.config, "DATA_NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(storage_module.config, "PROJECT_ROOT", tmp_path)
    storage_module.storage._npc_view = None
    storage_module.storage._scene_view = None


def _npc_paths():
    return storage_module.storage.npc_view(npc_id="vika", scene_id="default")


def _patch_prompt_loader(monkeypatch, tmp_path: Path, files: dict[str, str]) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        (prompts_dir / filename).write_text(content, encoding="utf-8")


def test_image_updater_schedule_generates_image_and_persists_prompt(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    _patch_prompt_loader(
        monkeypatch,
        tmp_path,
        {
            "image_build_prompt.md": "build\n{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}",
            "image_refresh.md": "refresh {{BASE_PROMPT}}",
        },
    )

    captured_prompt: dict[str, Any] = {"value": None}
    captured_render: dict[str, Any] = {"prompt": None, "current": None, "identity": None}

    def fake_refresh(prompt: str, current_img: bytes, identity_img: bytes | None = None) -> bytes:
        captured_render["prompt"] = prompt
        captured_render["current"] = current_img
        captured_render["identity"] = identity_img
        return b"generated"

    monkeypatch.setattr(
        character_image_service_module,
        "run_prompt_small",
        lambda prompt: captured_prompt.__setitem__("value", prompt) or "optimized prompt",
    )
    monkeypatch.setattr(character_image_service_module, "refresh_img", fake_refresh)

    updater = ImageUpdater()
    updater.emit_update()
    updater.schedule()

    assert _npc_paths().img_runtime.get().read_bytes() == b"generated"
    assert _npc_paths().image_prompt.get() == "optimized prompt"
    assert captured_render == {"prompt": "refresh optimized prompt", "current": b"ref", "identity": b"default"}
    assert captured_prompt["value"] == "build\n(none)\nstate\nscene"


def test_image_updater_schedule_skips_when_prompt_is_unchanged(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    _patch_prompt_loader(
        monkeypatch,
        tmp_path,
        {
            "image_build_prompt.md": "build rules",
            "image_refresh.md": "refresh {{BASE_PROMPT}}",
        },
    )

    updater = ImageUpdater()
    updater.emit_update()
    _npc_paths().image_prompt.path.parent.mkdir(parents=True, exist_ok=True)
    _npc_paths().image_prompt.save("same prompt")

    monkeypatch.setattr(character_image_service_module, "run_prompt_small", lambda _prompt: "same prompt")
    monkeypatch.setattr(
        character_image_service_module,
        "refresh_img",
        lambda _prompt, _img, _identity=None: (_ for _ in ()).throw(AssertionError("Image generation must not run")),
    )

    updater.schedule()

    assert _npc_paths().img_runtime.exists() is False


def test_image_updater_emit_update_if_missing_sets_trigger_when_runtime_image_is_missing(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()

    updater.emit_update_if_missing()

    assert updater._run_trigger_item().get() == "1"


def test_image_updater_emit_update_if_missing_skips_when_runtime_image_exists(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    updater = ImageUpdater()
    image_path = _npc_paths().img_runtime.path
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"generated")

    updater.emit_update_if_missing()

    assert updater._run_trigger_item().exists() is False


def test_image_updater_revert_returns_noop_when_no_image_and_no_backup(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    result = ImageUpdater().service.revert()

    assert result is None


def test_image_updater_revert_restores_backup_when_image_missing(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()
    image_path = _npc_paths().img_runtime.path
    backup_dir = _npc_paths().backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "img-20260323-130000.png"
    backup.write_bytes(b"restored")

    result = updater.service.revert()

    assert result is None
    assert image_path.read_bytes() == b"restored"
    assert backup.exists() is False


def test_image_updater_revert_deletes_image_and_restores_latest_backup(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)

    updater = ImageUpdater()
    image_path = _npc_paths().img_runtime.path
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"current")

    backup_dir = _npc_paths().backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "img-20260323-120000.png").write_bytes(b"old")
    new_backup = backup_dir / "img-20260323-130000.png"
    new_backup.write_bytes(b"new")

    result = updater.service.revert()

    assert result is None
    assert image_path.read_bytes() == b"new"
    assert new_backup.exists() is False


def test_image_updater_merge_with_scene_persists_merged_image(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    _patch_prompt_loader(
        monkeypatch,
        tmp_path,
        {
            "image_scene.md": "merge {{SCENE_DESCRIPTION}}",
            "image_build_prompt.md": "build\n{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}",
        },
    )

    captured: dict[str, object] = {"update_prompt_source": None}

    def fake_merge(prompt: str, character_img_bytes: bytes, scene_img_bytes: bytes) -> bytes:
        captured["prompt"] = prompt
        captured["character_img_bytes"] = character_img_bytes
        captured["scene_img_bytes"] = scene_img_bytes
        return b"merged-image"

    monkeypatch.setattr(character_image_service_module, "merge_character_scene_img", fake_merge)
    monkeypatch.setattr(
        character_image_service_module,
        "run_prompt_small",
        lambda prompt: captured.__setitem__("update_prompt_source", prompt) or "initial update prompt",
    )

    updater = ImageUpdater()
    image_path = _npc_paths().img_runtime.path
    prompt_path = _npc_paths().image_prompt.path
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"old-image")

    result = updater.service.merge_with_scene()

    assert result is None
    assert captured["prompt"] == "merge scene"
    assert captured["character_img_bytes"] == b"ref"
    assert captured["scene_img_bytes"] == b"scene"
    assert captured["update_prompt_source"] == "build\n(none)\nstate\nscene"
    assert image_path.read_bytes() == b"merged-image"
    assert prompt_path.read_text(encoding="utf-8") == "initial update prompt"


def test_image_updater_merge_with_scene_propagates_errors(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    _patch_prompt_loader(monkeypatch, tmp_path, {"image_scene.md": "merge {{SCENE_DESCRIPTION}}"})

    def failing_merge(_prompt: str, _character_img_bytes: bytes, _scene_img_bytes: bytes) -> bytes:
        raise RuntimeError("merge_failed")

    monkeypatch.setattr(character_image_service_module, "merge_character_scene_img", failing_merge)
    updater = ImageUpdater()

    try:
        updater.service.merge_with_scene()
        raise AssertionError("Expected RuntimeError")
    except RuntimeError as exc:
        assert str(exc) == "merge_failed"

    assert _npc_paths().img_runtime.exists() is False


def test_image_updater_schedule_uses_initial_merge_when_runtime_image_is_missing(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    _patch_prompt_loader(
        monkeypatch,
        tmp_path,
        {
            "image_scene.md": "merge {{SCENE_DESCRIPTION}}",
            "image_build_prompt.md": "build\n{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}",
        },
    )

    captured: dict[str, object] = {"update_prompt_source": None}

    def fake_merge(prompt: str, character_img_bytes: bytes, scene_img_bytes: bytes) -> bytes:
        captured["prompt"] = prompt
        captured["character_img_bytes"] = character_img_bytes
        captured["scene_img_bytes"] = scene_img_bytes
        return b"merged-image"

    monkeypatch.setattr(
        character_image_service_module,
        "run_prompt_small",
        lambda prompt: captured.__setitem__("update_prompt_source", prompt) or "initial update prompt",
    )
    monkeypatch.setattr(character_image_service_module, "merge_character_scene_img", fake_merge)
    monkeypatch.setattr(
        character_image_service_module,
        "refresh_img",
        lambda _prompt, _img, _identity=None: (_ for _ in ()).throw(AssertionError("refresh path must not run")),
    )

    updater = ImageUpdater()
    updater.emit_update()
    updater.schedule()

    assert _npc_paths().img_runtime.get().read_bytes() == b"merged-image"
    assert _npc_paths().image_prompt.get() == "initial update prompt"
    assert captured["prompt"] == "merge scene"
    assert captured["character_img_bytes"] == b"ref"
    assert captured["scene_img_bytes"] == b"scene"
    assert captured["update_prompt_source"] == "build\n(none)\nstate\nscene"


def test_image_updater_schedule_propagates_errors_without_exception_handling(tmp_path, monkeypatch):
    _patch_stores(monkeypatch, tmp_path)
    _patch_prompt_loader(
        monkeypatch,
        tmp_path,
        {
            "image_build_prompt.md": "{{CURRENT_IMAGE_PROMPT}}\n{{CURRENT_STATE}}\n{{CURRENT_SCENE}}",
            "image_refresh.md": "refresh {{BASE_PROMPT}}",
        },
    )

    prompts = iter(["first prompt", "second prompt"])
    monkeypatch.setattr(character_image_service_module, "run_prompt_small", lambda _prompt: next(prompts))

    def failing_refresh(_prompt: str, _img: bytes, _identity: bytes | None = None) -> bytes:
        raise RuntimeError("moderation_blocked")

    monkeypatch.setattr(character_image_service_module, "refresh_img", failing_refresh)

    updater = ImageUpdater()
    updater.emit_update()
    try:
        updater.schedule()
    except RuntimeError:
        pass

    monkeypatch.setattr(character_image_service_module, "refresh_img", lambda _prompt, _img, _identity=None: b"ok-image")
    updater.emit_update()
    updater.schedule()

    assert _npc_paths().img_runtime.get().read_bytes() == b"ok-image"
    assert _npc_paths().image_prompt.get() == "second prompt"
