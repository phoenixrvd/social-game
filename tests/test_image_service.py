from __future__ import annotations

from types import SimpleNamespace

import pytest

import engine.services.image_service as image_service_module
from engine.services.image_service import ImageService
from engine.storage.files import ImageFile, TextFile


def test_update_from_context_without_runtime_image_uses_initial_scene_description(monkeypatch, tmp_path) -> None:
    character_path = tmp_path / "character.png"
    scene_path = tmp_path / "scene.png"
    scene_original_path = tmp_path / "scene_original.md"
    npc_scene_path = tmp_path / "npc_scene.md"
    runtime_scene_path = tmp_path / "runtime_scene.md"

    character_path.write_bytes(b"character")
    scene_path.write_bytes(b"scene")
    scene_original_path.write_text("Basis: cremefarbenes Top", encoding="utf-8")
    npc_scene_path.write_text("NPC: helles Cardigan", encoding="utf-8")
    runtime_scene_path.write_text("Runtime: sitzt seitlich am Tisch", encoding="utf-8")

    saved_prompt: dict[str, str] = {}
    captured: dict[str, str] = {}

    fake_storage = SimpleNamespace(
        npc=SimpleNamespace(
            img_runtime=ImageFile(tmp_path / "data" / "img.png"),
            img=ImageFile(character_path),
            backup_dir=tmp_path / "backup",
            image_prompt=SimpleNamespace(save=lambda value: saved_prompt.update({"value": value})),
        ),
        scene=SimpleNamespace(
            description="Nur Runtime",
            img=scene_path,
            scene_original=TextFile(scene_original_path),
            npc_scene_original=TextFile(npc_scene_path),
            scene_runtime=TextFile(runtime_scene_path),
        ),
        prompts=SimpleNamespace(
            image_scene=SimpleNamespace(get=lambda: "{{IMAGE_STYLE_RULES}}\nSCENE\n{{SCENE_DESCRIPTION}}"),
            image_style_rules=SimpleNamespace(get=lambda: "STYLE"),
        ),
    )

    def merge_character_scene_img(prompt: str, _character: bytes, _scene: bytes) -> bytes:
        captured["prompt"] = prompt
        return b"generated"

    monkeypatch.setattr(image_service_module, "storage", fake_storage)
    monkeypatch.setattr(
        image_service_module,
        "client",
        SimpleNamespace(merge_character_scene_img=merge_character_scene_img),
    )
    monkeypatch.setattr(ImageService, "_generate_update_prompt", lambda self, npc, scene, old_prompt: "seed")

    service = ImageService()
    service.update_from_context()

    assert "Basis: cremefarbenes Top" in captured["prompt"]
    assert "NPC: helles Cardigan" in captured["prompt"]
    assert "Runtime: sitzt seitlich am Tisch" in captured["prompt"]
    assert "STYLE" in captured["prompt"]
    assert fake_storage.npc.img_runtime.get().read_bytes() == b"generated"
    assert saved_prompt["value"] == "seed"


def test_initial_scene_description_falls_back_to_scene_description_when_sources_are_empty(tmp_path) -> None:
    missing = tmp_path / "missing.md"
    scene = SimpleNamespace(
        scene_original=TextFile(missing),
        npc_scene_original=TextFile(tmp_path / "missing_npc.md"),
        scene_runtime=TextFile(tmp_path / "missing_runtime.md"),
        description="Fallback Beschreibung",
    )

    assert ImageService._initial_scene_description(scene) == "Fallback Beschreibung"  # type: ignore[arg-type]


def test_update_from_context_skips_same_normalized_visual_tokens(monkeypatch, tmp_path) -> None:
    image_path = ImageFile(tmp_path / "data" / "img.png")
    image_path.save(b"current")
    old_prompt = "portrait, red dress, standing by a window"
    new_prompt = "  standing   by a window, PORTRAIT, red dress "
    refreshed: list[str] = []

    fake_storage = SimpleNamespace(
        npc=SimpleNamespace(
            img_runtime=image_path,
            image_prompt=SimpleNamespace(exists=lambda: True, get=lambda: old_prompt),
        ),
        scene=SimpleNamespace(),
    )

    monkeypatch.setattr(image_service_module, "storage", fake_storage)
    monkeypatch.setattr(
        ImageService,
        "_generate_update_prompt",
        lambda self, npc, scene, old_prompt: new_prompt,
    )
    monkeypatch.setattr(
        ImageService,
        "_refresh_from_prompt",
        lambda self, npc, image_path, new_prompt: refreshed.append(new_prompt),
    )

    ImageService().update_from_context()

    assert refreshed == []
    assert image_path.get().read_bytes() == b"current"


def test_update_from_context_refreshes_for_changed_prompt(monkeypatch, tmp_path) -> None:
    image_path = ImageFile(tmp_path / "data" / "img.png")
    image_path.save(b"current")
    old_prompt = "portrait, red dress, standing by a window"
    new_prompt = "wide shot, blue coat, running through heavy rain"
    refreshed: list[str] = []

    fake_storage = SimpleNamespace(
        npc=SimpleNamespace(
            img_runtime=image_path,
            image_prompt=SimpleNamespace(exists=lambda: True, get=lambda: old_prompt),
        ),
        scene=SimpleNamespace(),
    )

    monkeypatch.setattr(image_service_module, "storage", fake_storage)
    monkeypatch.setattr(
        ImageService,
        "_generate_update_prompt",
        lambda self, npc, scene, old_prompt: new_prompt,
    )
    monkeypatch.setattr(
        ImageService,
        "_refresh_from_prompt",
        lambda self, npc, image_path, new_prompt: refreshed.append(new_prompt),
    )

    ImageService().update_from_context()

    assert refreshed == [new_prompt]


@pytest.mark.parametrize(
    ("old_prompt", "new_prompt", "expected"),
    [
        (
            "portrait, red dress, standing by a window",
            "  standing   by a window, PORTRAIT, red dress ",
            True,
        ),
        (
            "portrait, red dress, standing by a window, soft light",
            "portrait, red dress, standing by a window, soft light, scar on cheek",
            False,
        ),
        (
            "portrait, red dress, silver necklace, standing by a window, soft light",
            "portrait, standing by a window, soft light",
            False,
        ),
        (
            "portrait, red dress, soft light, standing by a window with city view",
            "portrait, red dress, soft light, standing by the window with city view",
            False,
        ),
    ],
)
def test_prompt_skip_uses_exact_normalized_visual_tokens(
    old_prompt: str,
    new_prompt: str,
    expected: bool,
) -> None:
    assert ImageService._should_skip_prompt_update(new_prompt, old_prompt, force=False) is expected
