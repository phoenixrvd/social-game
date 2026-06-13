from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Path
from fastapi.responses import Response
from pydantic import Field

from engine.api import history as history_api
from engine.api.models import ApiModel, LONG_TEXT_MAX_LENGTH, SHORT_TEXT_MAX_LENGTH, USER_PROFILE_MAX_LENGTH
from engine.api.state_app import EntityId, RelativeUrl, url_version
from engine.config import config
from engine.services.image_codec import cached_webp_bytes, is_image_backup_name
from engine.services.image_service import ImageService
from engine.services.npc_scene_service import NpcSceneService
from engine.services.scene_service import SceneService
from engine.storage import storage
from engine.tools.scheduler import get_scheduler as _get_scheduler

from .state_npc import messages_signature, visible_messages

get_scheduler = _get_scheduler

router = APIRouter(tags=["session"])


class SessionRequest(ApiModel):
    npc: EntityId | None = Field(default=None, description="Neue aktive NPC-ID; bleibt unverändert, wenn das Feld fehlt oder null ist.")
    scene: EntityId | None = Field(
        default=None,
        description="Neue aktive Szenen-ID; bleibt unverändert, wenn das Feld fehlt oder null ist.",
    )
    avatar: EntityId | None = Field(
        default=None,
        description="Neue aktive Avatar-ID; bleibt unverändert, wenn das Feld fehlt oder null ist.",
    )
    image_autogenerate: bool | None = Field(
        default=None,
        description="Schaltet automatische Bildgenerierung für Folgeschritte ein oder aus; bleibt unverändert, wenn das Feld fehlt oder null ist.",
    )


class UserProfileRequest(ApiModel):
    content: str = Field(
        max_length=USER_PROFILE_MAX_LENGTH,
        description="Vollständiger Profiltext der Nutzerin oder des Nutzers, der den bisherigen Profiltext ersetzt.",
    )


class ImageBackupResponse(ApiModel):
    name: str = Field(description="Dateiname des Backup-Bildes; kann zum Laden dieses Backups verwendet werden.")
    url: RelativeUrl = Field(description="Relative URL zum Laden des Backup-Bildes.")
    signature: str = Field(description="Signatur zur Erkennung von Bildänderungen.")


class ImageSignatureResponse(ApiModel):
    signature: str = Field(description="Änderungssignatur des aktiven Bildes; leer, wenn keine Datei existiert.")
    image_is_original: bool = Field(description="Gibt an, ob das aktive Bild dem initialen NPC-Bild entspricht.")


class EmptyResponse(ApiModel):
    pass


class SceneContextRequest(ApiModel):
    content: str = Field(
        max_length=LONG_TEXT_MAX_LENGTH,
        description="Textgrundlage für die Generierung oder vollständiger Inhalt des zu speichernden Szenenkontexts.",
    )


class SceneContextResponse(ApiModel):
    context: str = Field(description="Generierter NPC-spezifischer Szenenkontext, der vor dem Speichern noch bearbeitet werden kann.")


class MessageResponse(ApiModel):
    id: str = Field(description="Stabile Nachrichten-ID aus dem Laufzeitspeicher oder synthetische Kontext-ID.")
    role: Literal["user", "assistant", "system"] = Field(description="Rolle der Nachricht im Dialogverlauf.")
    content: str = Field(description="Rohtext der Nachricht; bei gerenderten Kontextkarten kann dieser leer sein.")
    timestamp_utc: datetime = Field(description="UTC-Zeitpunkt der Nachricht oder der synthetischen Kontextkarte.")
    html: str | None = Field(default=None, description="Optional gerenderter HTML-Inhalt für Kontextkarten.")
    context_type: Literal["scene"] | None = Field(default=None, description="Markiert eine Nachricht als Szenenkontext, falls gesetzt.")
    is_editable_scene_context: bool | None = Field(
        default=None,
        description="Gibt an, ob die Oberfläche diesen Szenenkontext direkt bearbeiten darf.",
    )


class StateResponse(ApiModel):
    npc: EntityId = Field(description="Aktive NPC-ID der Session.")
    scene: EntityId = Field(description="Aktive Szenen-ID der Session.")
    avatar: EntityId = Field(description="Aktive Avatar-ID der Session.")
    scene_context: str = Field(description="Aktueller NPC-spezifischer Kontext zur aktiven Szene.")
    messages: list[MessageResponse] = Field(description="Für die Oberfläche sichtbare Dialog- und Kontextnachrichten.")
    messages_signature: str = Field(description="Kurze Signatur des sichtbaren Dialogverlaufs zur Änderungserkennung.")
    image_signature: str = Field(description="Kurze Signatur des aktiven Laufzeitbildes zur Änderungserkennung.")
    image_is_original: bool = Field(description="Gibt an, ob das aktive Bild dem initialen NPC-Bild entspricht.")
    user_profile: str = Field(description="Aktuelles Laufzeitprofil der Nutzerin oder des Nutzers.")
    image_autogenerate: bool = Field(description="Gibt an, ob das Bild nach passenden Änderungen automatisch aktualisiert wird.")
    default_npc: EntityId = Field(description="Konfigurierte Standard-NPC-ID.")
    default_scene: EntityId = Field(description="Konfigurierte Standard-Szenen-ID.")
    default_avatar: EntityId = Field(description="Konfigurierte Standard-Avatar-ID.")
    can_reset_scene: bool = Field(description="Gibt an, ob die aktive Szene zurückgesetzt werden kann.")


CommitHash = Annotated[str, Path(min_length=7, pattern=r"^[0-9a-fA-F]{7,40}$", description="Git-Commit-Hash.")]
ImageBackupName = Annotated[
    str,
    Path(max_length=SHORT_TEXT_MAX_LENGTH, pattern=r"^img-\d{8}-\d{6}\.png$", description="Name eines Bild-Backups."),
]


class OperationResponse(ApiModel):
    success: bool = Field(description="Gibt an, ob die Operation erfolgreich war.")


class CheckpointResponse(ApiModel):
    commit_hash: CommitHash = Field(description="Git-Commit-Hash des gespeicherten Checkpoints.")
    commit_date: datetime = Field(description="Zeitpunkt des Checkpoint-Commits.")
    commit_message: str = Field(description="Commit-Nachricht, die den Checkpoint beschreibt.")


class CheckpointListResponse(ApiModel):
    checkpoints: list[CheckpointResponse] = Field(description="Verfügbare Checkpoints.")


@router.get("/api/session", summary="App-State laden")
def get_state() -> StateResponse:
    """Liefert den vollständigen App-State für die Oberfläche. Die Antwort enthält aktive IDs, Kontext, sichtbare Nachrichten, Bildstatus, Profil, Standardauswahl und Reset-Fähigkeiten."""

    return _state_response()


@router.put("/api/session", summary="Session aktualisieren")
def update_session(request: SessionRequest) -> StateResponse:
    """Aktualisiert nur die im Request gesetzten Session-Werte und liefert danach den vollständigen App-State. Beim Einschalten der automatischen Bildgenerierung wird das Bild anschließend aktualisiert."""

    if request.npc is not None:
        storage.session.npc_id = request.npc
    if request.scene is not None:
        storage.session.scene_id = request.scene
    if request.avatar is not None:
        storage.session.avatar_id = request.avatar
    if request.image_autogenerate is not None:
        storage.session.image_autogenerate = request.image_autogenerate
    if request.image_autogenerate:
        get_scheduler().enqueue("image")
    if request.npc is not None or request.scene is not None:
        NpcSceneService().adapt_default_fallback()
    return _state_response()


@router.post("/api/session/context/generate", summary="Szenenkontext generieren")
def scene_context_generate(request: SceneContextRequest) -> SceneContextResponse:
    """Erzeugt einen NPC-spezifischen Szenenkontext aus der übergebenen Textgrundlage. Der generierte Text wird nur zurückgegeben und nicht automatisch gespeichert."""

    return SceneContextResponse(context=NpcSceneService().generate_context(request.content))


@router.put("/api/session/context", summary="Szenenkontext speichern")
def scene_context_update(request: SceneContextRequest) -> StateResponse:
    """Speichert den übergebenen Text als NPC-spezifischen Kontext der aktiven Szene und liefert den aktualisierten App-State zurück."""

    NpcSceneService().save_active_context(request.content)
    return _state_response()


@router.get("/api/session/history", summary="Checkpoints auflisten")
def history_checkpoints() -> CheckpointListResponse:
    """Liefert alle verfügbaren Checkpoints mit Kennung, Datum und Nachricht. Die Kennung kann zum Wiederherstellen eines Checkpoints verwendet werden."""

    checkpoints = history_api.checkpoints()
    return CheckpointListResponse(
        checkpoints=[
            CheckpointResponse(
                commit_hash=checkpoint.commit_hash,
                commit_date=checkpoint.commit_date,
                commit_message=checkpoint.commit_message,
            )
            for checkpoint in checkpoints
        ]
    )


@router.post("/api/session/history", summary="Checkpoint speichern")
def history_create_checkpoint() -> OperationResponse:
    """Speichert den aktuellen Zustand als Checkpoint und meldet den Erfolg der Operation."""

    history_api.create()
    return OperationResponse(success=True)


@router.post("/api/session/history/{commit_hash}/restore", summary="Checkpoint wiederherstellen")
def history_restore_checkpoint(commit_hash: CommitHash) -> OperationResponse:
    """Stellt den Zustand aus dem angegebenen Checkpoint wieder her. Der Pfadparameter muss eine gültige Checkpoint-Kennung mit 7 bis 40 Hex-Zeichen sein."""

    history_api.restore(commit_hash)
    return OperationResponse(success=True)


@router.get("/api/session/image", summary="Aktives Laufzeitbild laden")
def image_current() -> Response:
    """Liefert das aktive Bild des aktuellen NPC-Szenen-Kontexts als WebP. Wenn kein aktualisiertes Bild existiert, wird das initiale Bild verwendet."""

    return _webp_response(storage.npc.img.get())


@router.get("/api/session/image/backups", summary="Bild-Backups auflisten")
def image_current_backups() -> list[ImageBackupResponse]:
    """Liefert die verfügbaren Backups des aktiven Laufzeitbildes mit Lade-URL und Signatur. Die Backups gehören immer zum aktuellen NPC-Szenen-Kontext."""

    return [
        ImageBackupResponse(
            name=image.name,
            url=f"/api/session/image/backups/{image.name}?v={url_version(image.get())}",
            signature=_file_signature(image.get()),
        )
        for image in storage.npc.img_backup
    ]


@router.get("/api/session/image/backups/{backup_name}", summary="Bild-Backup laden")
def image_current_backup(backup_name: ImageBackupName) -> Response:
    """Liefert ein benanntes Backup des aktiven Laufzeitbildes als WebP. Ungültige oder nicht vorhandene Backup-Namen werden aus Sicherheitsgründen mit 404 beantwortet."""

    if not is_image_backup_name(backup_name):
        raise HTTPException(status_code=404, detail="Backup-Bild nicht gefunden.")
    backup_image = next((img for img in storage.npc.img_backup if img.name == backup_name), None)
    if backup_image is None:
        raise HTTPException(status_code=404, detail="Backup-Bild nicht gefunden.")
    return _webp_response(backup_image.get())


@router.delete("/api/session/image", summary="Aktives Laufzeitbild löschen, Initialbild verwenden")
def image_current_delete() -> Response:
    """Löscht nur das aktive Laufzeitbild des aktuellen NPC-Szenen-Kontexts. Danach greift die Oberfläche wieder auf das Initialbild zurück; vorhandene Backups bleiben erhalten."""

    ImageService().delete_current()
    return Response(status_code=200)


@router.post("/api/session/image/refresh", summary="Aktives Laufzeitbild aktualisieren")
def image_current_refresh() -> EmptyResponse:
    """Erzeugt das aktive Bild aus dem aktuellen NPC-Szenen-Kontext neu und überschreibt den bisherigen aktiven Bildstand."""

    ImageService().update_from_context(force=True)
    return EmptyResponse()


@router.post("/api/session/image/revert", summary="Auf letztes Backup zurücksetzen")
def image_current_revert() -> EmptyResponse:
    """Setzt das aktive Laufzeitbild auf das letzte verfügbare Backup des aktuellen NPC-Szenen-Kontexts zurück."""

    ImageService().revert()
    return EmptyResponse()


@router.get("/api/session/image/signature", summary="Bildsignatur abrufen")
def image_current_signature() -> ImageSignatureResponse:
    """Liefert eine kompakte Signatur und die Herkunft des aktiven Bildzustands, damit die Oberfläche Bildänderungen ohne erneutes Laden des App-State erkennen kann."""

    npc = storage.npc
    return ImageSignatureResponse(
        signature=_file_signature(npc.img.get()),
        image_is_original=npc.is_image_original,
    )


@router.put("/api/session/user-profile", summary="Nutzerprofil speichern")
def update_user_profile(request: UserProfileRequest) -> StateResponse:
    """Ersetzt das Laufzeit-Nutzerprofil des aktuellen NPC-Szenen-Kontexts durch den übergebenen Text und liefert danach den vollständigen App-State."""

    storage.npc.user_profile_runtime.save(request.content)
    return _state_response()


def _webp_response(image_path, max_width: int | None = None) -> Response:
    return Response(content=cached_webp_bytes(image_path, max_width=max_width), media_type="image/webp")


def _file_signature(path) -> str:
    if not path.exists():
        return ""
    stat = path.stat()
    return f"{stat.st_mtime_ns}|{stat.st_size}"


def _state_response() -> StateResponse:
    npc = storage.npc
    scene = storage.scene
    avatar = storage.avatar
    return StateResponse(
        npc=npc.npc_id,
        scene=scene.scene_id,
        avatar=avatar.avatar_id,
        scene_context=scene.npc_context.original.get(),
        messages=[MessageResponse(**message) for message in visible_messages(npc, scene)],
        messages_signature=messages_signature(npc),
        image_signature=_file_signature(npc.img.get()),
        image_is_original=npc.is_image_original,
        user_profile=avatar.description.get(),
        image_autogenerate=storage.session.image_autogenerate,
        default_npc=config.DEFAULT_NPC_ID,
        default_scene=config.DEFAULT_SCENE_ID,
        default_avatar=config.DEFAULT_AVATAR_ID,
        can_reset_scene=SceneService.can_reset_active_scene(),
    )
