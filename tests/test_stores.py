from types import SimpleNamespace

import engine.storage as storage_module
from engine.storage import Message


def _patch_storage(monkeypatch, tmp_path, session_provider) -> None:
    monkeypatch.setattr(storage_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(storage_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(storage_module.config, "DATA_NPC_DIR", tmp_path / "data" / "npcs")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(
        storage_module.SessionStorageItem,
        "get",
        lambda _self: session_provider(),
    )


def test_storage_loads_and_saves_scene(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, lambda: SimpleNamespace(npc_id="vika", scene_id="default"))

    (tmp_path / "scenes" / "default").mkdir(parents=True)
    (tmp_path / "scenes" / "default" / "scene.md").write_text("# Default Szene", encoding="utf-8")
    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / "npcs" / "vika" / "description.md").write_text("NPC", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "state.md").write_text("mood: neutral", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "relationship.md").write_text("", encoding="utf-8")

    assert storage_module.storage.scene.scene_id == "default"
    assert "Default Szene" in storage_module.storage.scene.description

    storage_module.storage.scene.scene_runtime.save("# Testbeschreibung\nDie Szene wurde aktualisiert.")
    assert "Testbeschreibung" in storage_module.storage.scene.description


def test_storage_keeps_runtime_data_separated_per_scene(tmp_path, monkeypatch):
    current_scene = {"value": "office"}

    def session_provider() -> SimpleNamespace:
        return SimpleNamespace(npc_id="vika", scene_id=current_scene["value"])

    _patch_storage(monkeypatch, tmp_path, session_provider)

    for scene_id in ("office", "cafe"):
        (tmp_path / "scenes" / scene_id).mkdir(parents=True, exist_ok=True)
        (tmp_path / "scenes" / scene_id / "scene.md").write_text(f"# {scene_id}", encoding="utf-8")

    npc_dir = tmp_path / "npcs" / "vika"
    npc_dir.mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("mood: neutral", encoding="utf-8")
    (npc_dir / "relationship.md").write_text("", encoding="utf-8")

    storage_module.storage.npc.state_runtime.save("mood: office")
    current_scene["value"] = "cafe"
    storage_module.storage.npc.state_runtime.save("mood: cafe")
    current_scene["value"] = "office"
    storage_module.storage.npc.stm.append(Message(id="1", timestamp_utc="2026-03-22T10:00:00+00:00", role="user", content="hi office"))
    storage_module.storage.npc.stm.append(Message(id="2", timestamp_utc="2026-03-22T10:00:01+00:00", role="assistant", content="reply office"))
    current_scene["value"] = "cafe"
    storage_module.storage.npc.stm.append(Message(id="3", timestamp_utc="2026-03-22T10:00:02+00:00", role="user", content="hi cafe"))
    storage_module.storage.npc.stm.append(Message(id="4", timestamp_utc="2026-03-22T10:00:03+00:00", role="assistant", content="reply cafe"))

    current_scene["value"] = "office"
    assert storage_module.storage.npc.state == "mood: office"
    assert [msg.content for msg in storage_module.storage.npc.stm.get()] == ["hi office", "reply office"]

    current_scene["value"] = "cafe"
    assert storage_module.storage.npc.state == "mood: cafe"
    assert [msg.content for msg in storage_module.storage.npc.stm.get()] == ["hi cafe", "reply cafe"]


def test_storage_image_falls_back_to_npc_root_image(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, lambda: SimpleNamespace(npc_id="mira", scene_id="office"))

    for scene_id in ("office", "departure"):
        (tmp_path / "scenes" / scene_id).mkdir(parents=True, exist_ok=True)
        (tmp_path / "scenes" / scene_id / "scene.md").write_text(f"# {scene_id}", encoding="utf-8")

    npc_dir = tmp_path / "npcs" / "mira"
    (npc_dir / "scenes" / "departure").mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Mira\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("mood: neutral", encoding="utf-8")
    (npc_dir / "relationship.md").write_text("", encoding="utf-8")
    (npc_dir / "scenes" / "departure" / "img.png").write_bytes(b"img")
    (npc_dir / "img.png").write_bytes(b"root-img")

    assert storage_module.storage.npc.img_current.get() == npc_dir / "img.png"


def test_storage_runtime_scene_and_relationship_bootstrap(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, lambda: SimpleNamespace(npc_id="vika", scene_id="default"))

    (tmp_path / "scenes" / "default").mkdir(parents=True)
    (tmp_path / "scenes" / "default" / "scene.md").write_text("# Default Szene", encoding="utf-8")
    npc_dir = tmp_path / "npcs" / "vika"
    npc_dir.mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("mood: neutral", encoding="utf-8")
    (npc_dir / "relationship.md").write_text("relationship-default", encoding="utf-8")

    storage_module.storage.scene.scene_runtime.save("Runtime Szene")
    assert "Runtime Szene" in storage_module.storage.scene.description
    assert storage_module.storage.npc.relationship.get() == "relationship-default"
    assert storage_module.storage.npc.state == "mood: neutral\n\nrelationship-default"


def test_storage_prefers_data_then_overrides_then_default(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, lambda: SimpleNamespace(npc_id="vika", scene_id="default"))

    (tmp_path / "scenes" / "default").mkdir(parents=True)
    (tmp_path / "scenes" / "default" / "scene.md").write_text("Default Scene", encoding="utf-8")

    npc_dir = tmp_path / "npcs" / "vika"
    npc_dir.mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("state-default", encoding="utf-8")
    (npc_dir / "relationship.md").write_text("relationship-default", encoding="utf-8")

    overrides_npc = tmp_path / ".overrides" / "npcs" / "vika"
    overrides_npc.mkdir(parents=True)
    (overrides_npc / "state.md").write_text("state-override", encoding="utf-8")
    (overrides_npc / "relationship.md").write_text("relationship-override", encoding="utf-8")

    assert storage_module.storage.npc.state == "state-override\n\nrelationship-override"
    assert storage_module.storage.npc.relationship.get() == "relationship-override"

    storage_module.storage.npc.state_runtime.save("state-runtime")
    assert storage_module.storage.npc.state == "state-runtime"
    assert storage_module.storage.npc.relationship.get() == "relationship-override"
