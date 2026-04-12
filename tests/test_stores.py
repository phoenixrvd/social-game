import engine.storage as storage_module
import engine.stores.session_store as session_store_module
from engine.models import Session
from engine.stores.npc_store import NpcStore


class FakeSessionStore:
    def load(self) -> Session:
        return Session(npc_id="vika", scene_id="default")


def _patch_storage(monkeypatch, tmp_path, session_store_cls) -> None:
    monkeypatch.setattr(storage_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(storage_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(storage_module.config, "DATA_NPC_DIR", tmp_path / "data" / "npcs")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(storage_module.config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(session_store_module, "SessionStore", session_store_cls)
    storage_module.storage._npc_view = None
    storage_module.storage._scene_view = None


def test_npc_store_loads_and_saves_scene(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, FakeSessionStore)

    (tmp_path / "scenes" / "default").mkdir(parents=True)
    (tmp_path / "scenes" / "default" / "scene.md").write_text(
        "# Default Szene",
        encoding="utf-8",
    )
    (tmp_path / "npcs" / "vika").mkdir(parents=True)
    (tmp_path / "npcs" / "vika" / "description.md").write_text("NPC", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "state.md").write_text("mood: neutral", encoding="utf-8")
    (tmp_path / "npcs" / "vika" / "relationship.md").write_text("", encoding="utf-8")

    store = NpcStore()
    npc = store.load()

    assert npc.scene.scene_id == "default"
    assert "Default Szene" in npc.scene.description

    storage_module.storage.scene.scene_runtime.save("# Testbeschreibung\nDie Szene wurde aktualisiert.")

    reloaded = store.load()
    assert "Testbeschreibung" in reloaded.scene.description


def test_npc_store_keeps_runtime_data_separated_per_scene(tmp_path, monkeypatch):
    class SwitchableSessionStore:
        current_scene = "office"

        def load(self) -> Session:
            return Session(npc_id="vika", scene_id=type(self).current_scene)

    _patch_storage(monkeypatch, tmp_path, SwitchableSessionStore)

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

    store = NpcStore()
    storage_module.storage.npc.state_runtime.save("mood: office")
    SwitchableSessionStore.current_scene = "cafe"
    storage_module.storage.npc.state_runtime.save("mood: cafe")
    SwitchableSessionStore.current_scene = "office"
    store.append_stm_turn("hi office", "reply office")
    SwitchableSessionStore.current_scene = "cafe"
    store.append_stm_turn("hi cafe", "reply cafe")

    SwitchableSessionStore.current_scene = "office"
    office_npc = store.load()
    assert office_npc.state == "mood: office"
    assert [msg.content for msg in office_npc.stm] == ["hi office", "reply office"]

    SwitchableSessionStore.current_scene = "cafe"
    cafe_npc = store.load()
    assert cafe_npc.state == "mood: cafe"
    assert [msg.content for msg in cafe_npc.stm] == ["hi cafe", "reply cafe"]


def test_npc_store_image_falls_back_to_npc_root_image(tmp_path, monkeypatch):
    class SessionWithMissingSceneImage:
        def load(self) -> Session:
            return Session(npc_id="mira", scene_id="office")

    _patch_storage(monkeypatch, tmp_path, SessionWithMissingSceneImage)

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

    store = NpcStore()
    npc = store.load()

    assert npc.img_current == npc_dir / "img.png"


def test_npc_store_runtime_scene_and_relationship_bootstrap(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, FakeSessionStore)

    (tmp_path / "scenes" / "default").mkdir(parents=True)
    (tmp_path / "scenes" / "default" / "scene.md").write_text("# Default Szene", encoding="utf-8")
    npc_dir = tmp_path / "npcs" / "vika"
    npc_dir.mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("mood: neutral", encoding="utf-8")
    (npc_dir / "relationship.md").write_text("relationship-default", encoding="utf-8")

    store = NpcStore()
    storage_module.storage.scene.scene_runtime.save("Runtime Szene")
    reloaded = store.load()
    assert "Runtime Szene" in reloaded.scene.description
    assert reloaded.relationship == "relationship-default"
    assert reloaded.state == "mood: neutral\n\nrelationship-default"


def test_npc_store_prefers_data_then_overrides_then_default(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, FakeSessionStore)

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

    store = NpcStore()
    loaded = store.load()
    assert loaded.state == "state-override\n\nrelationship-override"
    assert loaded.relationship == "relationship-override"

    storage_module.storage.npc.state_runtime.save("state-runtime")
    runtime_loaded = store.load()
    assert runtime_loaded.state == "state-runtime"
    assert runtime_loaded.relationship == "relationship-override"

