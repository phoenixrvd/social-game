from types import SimpleNamespace

from engine.config import config
from engine.storage import storage
from engine.storage.models import Message


def _patch_storage(monkeypatch, tmp_path, session_provider) -> None:
    monkeypatch.setattr(config, "SCENE_DIR", tmp_path / "scenes")
    monkeypatch.setattr(config, "NPC_DIR", tmp_path / "npcs")
    monkeypatch.setattr(config, "DATA_NPC_DIR", tmp_path / "data" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_NPC_DIR", tmp_path / ".overrides" / "npcs")
    monkeypatch.setattr(config, "OVERRIDES_SCENE_DIR", tmp_path / ".overrides" / "scenes")
    monkeypatch.setattr(config, "SESSION_PATH", tmp_path / "session.yaml")
    session = session_provider()
    (tmp_path / "session.yaml").write_text(
        f"npc_id: {session.npc_id}\nscene_id: {session.scene_id}\n",
        encoding="utf-8",
    )


def _set_scene(tmp_path, current_scene: dict[str, str], scene_id: str) -> None:
    current_scene["value"] = scene_id
    (tmp_path / "session.yaml").write_text(
        f"npc_id: vika\nscene_id: {scene_id}\n",
        encoding="utf-8",
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

    assert storage.scene.scene_id == "default"
    assert "Default Szene" in storage.scene.description

    storage.scene.location.runtime.save("# Testbeschreibung\nDie Szene wurde aktualisiert.")
    assert "Testbeschreibung" in storage.scene.description


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

    storage.npc.state_runtime.save("mood: office")
    _set_scene(tmp_path, current_scene, "cafe")
    storage.npc.state_runtime.save("mood: cafe")
    _set_scene(tmp_path, current_scene, "office")
    storage.npc.stm.append(Message(id="1", timestamp_utc="2026-03-22T10:00:00+00:00", role="user", content="hi office"))
    storage.npc.stm.append(Message(id="2", timestamp_utc="2026-03-22T10:00:01+00:00", role="assistant", content="reply office"))
    _set_scene(tmp_path, current_scene, "cafe")
    storage.npc.stm.append(Message(id="3", timestamp_utc="2026-03-22T10:00:02+00:00", role="user", content="hi cafe"))
    storage.npc.stm.append(Message(id="4", timestamp_utc="2026-03-22T10:00:03+00:00", role="assistant", content="reply cafe"))

    _set_scene(tmp_path, current_scene, "office")
    assert storage.npc.state == "mood: office"
    assert [msg.content for msg in storage.npc.stm.get()] == ["hi office", "reply office"]

    _set_scene(tmp_path, current_scene, "cafe")
    assert storage.npc.state == "mood: cafe"
    assert [msg.content for msg in storage.npc.stm.get()] == ["hi cafe", "reply cafe"]


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
    (npc_dir / "scenes" / "departure" / "img.png").write_bytes(b"img")
    (npc_dir / "img.png").write_bytes(b"root-img")

    assert storage.npc.img.get() == npc_dir / "img.png"


def test_storage_runtime_scene_and_state_bootstrap(tmp_path, monkeypatch):
    _patch_storage(monkeypatch, tmp_path, lambda: SimpleNamespace(npc_id="vika", scene_id="default"))

    (tmp_path / "scenes" / "default").mkdir(parents=True)
    (tmp_path / "scenes" / "default" / "scene.md").write_text("# Default Szene", encoding="utf-8")
    npc_dir = tmp_path / "npcs" / "vika"
    npc_dir.mkdir(parents=True)
    (npc_dir / "description.md").write_text("NPC", encoding="utf-8")
    (npc_dir / "system_prompt.md").write_text("SYSTEM", encoding="utf-8")
    (npc_dir / "character.yaml").write_text("name: Vika\n", encoding="utf-8")
    (npc_dir / "state.md").write_text("mood: neutral", encoding="utf-8")

    storage.scene.location.runtime.save("Runtime Szene")
    assert "Runtime Szene" in storage.scene.description
    assert storage.npc.state == "mood: neutral"


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

    overrides_npc = tmp_path / ".overrides" / "npcs" / "vika"
    overrides_npc.mkdir(parents=True)
    (overrides_npc / "state.md").write_text("state-override", encoding="utf-8")

    assert storage.npc.state == "state-override"

    storage.npc.state_runtime.save("state-runtime")
    assert storage.npc.state == "state-runtime"
