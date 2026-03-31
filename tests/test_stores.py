import engine.stores.npc_store as npc_store_module
from engine.stores.npc_store import NpcStore
from engine.models import Session


class FakeSessionStore:
    def load(self) -> Session:
        return Session(npc_id="vika", scene_id="default")


def test_npc_store_loads_and_saves_scene(tmp_path, monkeypatch):
    monkeypatch.setattr(npc_store_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(npc_store_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(npc_store_module.config, "DATA_NPC_DIR", tmp_path / "data" / "npcs")
    monkeypatch.setattr(npc_store_module, "SessionStore", FakeSessionStore)

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
    (tmp_path / "npcs" / "vika" / "ltm.md").write_text("", encoding="utf-8")

    store = NpcStore()
    npc = store.load()

    assert npc.scene.scene_id == "default"
    assert "Default Szene" in npc.scene.description

    store.save_scene("vika", "default", "# Testbeschreibung\nDie Szene wurde aktualisiert.")

    reloaded = store.load()
    assert "Testbeschreibung" in reloaded.scene.description


def test_npc_store_keeps_runtime_data_separated_per_scene(tmp_path, monkeypatch):
    monkeypatch.setattr(npc_store_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(npc_store_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(npc_store_module.config, "DATA_NPC_DIR", tmp_path / "data" / "npcs")

    class SwitchableSessionStore:
        current_scene = "office"

        def load(self) -> Session:
            return Session(npc_id="vika", scene_id=type(self).current_scene)

    monkeypatch.setattr(npc_store_module, "SessionStore", SwitchableSessionStore)

    for scene_id in ("office", "cafe"):
        (tmp_path / "scenes" / scene_id).mkdir(parents=True, exist_ok=True)
        (tmp_path / "scenes" / scene_id / "scene.md").write_text(f"# {scene_id}", encoding="utf-8")

    npc_dir = tmp_path / "npcs" / "vika"
    npc_dir.mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("mood: neutral", encoding="utf-8")
    (npc_dir / "ltm.md").write_text("", encoding="utf-8")

    store = NpcStore()
    store.save_state("vika", "office", "mood: office")
    store.save_state("vika", "cafe", "mood: cafe")
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
    monkeypatch.setattr(npc_store_module.config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(npc_store_module.config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(npc_store_module.config, "DATA_NPC_DIR", tmp_path / "data" / "npcs")

    class SessionWithMissingSceneImage:
        def load(self) -> Session:
            return Session(npc_id="mira", scene_id="office")

    monkeypatch.setattr(npc_store_module, "SessionStore", SessionWithMissingSceneImage)

    for scene_id in ("office", "departure"):
        (tmp_path / "scenes" / scene_id).mkdir(parents=True, exist_ok=True)
        (tmp_path / "scenes" / scene_id / "scene.md").write_text(f"# {scene_id}", encoding="utf-8")

    npc_dir = tmp_path / "npcs" / "mira"
    (npc_dir / "scenes" / "departure").mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Mira\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("mood: neutral", encoding="utf-8")
    (npc_dir / "ltm.md").write_text("", encoding="utf-8")
    (npc_dir / "scenes" / "departure" / "img.png").write_bytes(b"img")
    (npc_dir / "img.png").write_bytes(b"root-img")

    store = NpcStore()
    npc = store.load()

    assert npc.img == npc_dir / "img.png"

