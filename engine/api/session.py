from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Path
from fastapi.responses import Response
from pydantic import Field

from engine.api import history as history_api
from engine.api.models import ApiModel
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
    npc: EntityId | None = Field(default=None, description="Neue aktive NPC-ID.")
    scene: EntityId | None = Field(default=None, description="Neue aktive Szenen-ID.")
    image_autogenerate: bool | None = Field(default=None, description="Automatische Bildgenerierung ein- oder ausschalten.")


class UserProfileRequest(ApiModel):
    content: str = Field(description="Profiltext der Nutzerin oder des Nutzers.")


class ImageBackupResponse(ApiModel):
    name: str
    url: RelativeUrl
    signature: str


class ImageSignatureResponse(ApiModel):
    signature: str
    image_is_original: bool


class EmptyResponse(ApiModel):
    pass


class SceneContextRequest(ApiModel):
    content: str = Field(description="Textgrundlage oder Inhalt des NPC-spezifischen Szenenkontexts.")


class SceneContextResponse(ApiModel):
    context: str = Field(description="Generierter NPC-spezifischer Szenenkontext.")


class MessageResponse(ApiModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp_utc: datetime
    html: str | None = None
    context_type: Literal["scene"] | None = None
    is_editable_scene_context: bool | None = None


class StateResponse(ApiModel):
    npc: EntityId
    scene: EntityId
    scene_context: str
    messages: list[MessageResponse]
    messages_signature: str
    image_signature: str
    user_profile: str
    image_autogenerate: bool
    default_npc: EntityId
    default_scene: EntityId
    can_reset_scene: bool


CommitHash = Annotated[str, Path(min_length=7, pattern=r"^[0-9a-fA-F]{7,40}$", description="Git-Commit-Hash.")]


class OperationResponse(ApiModel):
    success: bool = Field(description="Gibt an, ob die Operation erfolgreich war.")


class CheckpointResponse(ApiModel):
    commit_hash: CommitHash
    commit_date: datetime
    commit_message: str


class CheckpointListResponse(ApiModel):
    checkpoints: list[CheckpointResponse]


@router.get("/api/session", summary="App-State laden")
def get_state() -> StateResponse:
    """Liefert den aktuellen App-State für die Oberfläche."""

    return _state_response()


@router.put("/api/session", summary="Session aktualisieren")
def update_session(request: SessionRequest) -> StateResponse:
    """Aktualisiert Session-Werte und liefert den aktuellen App-State."""

    if request.npc is not None:
        storage.session.npc_id = request.npc
    if request.scene is not None:
        storage.session.scene_id = request.scene
    if request.image_autogenerate is not None:
        storage.session.image_autogenerate = request.image_autogenerate
    if request.image_autogenerate:
        get_scheduler().enqueue("image")
    if request.npc is not None or request.scene is not None:
        NpcSceneService().adapt_default_fallback()
    return _state_response()


@router.post("/api/session/context/generate", summary="Szenenkontext generieren")
def scene_context_generate(request: SceneContextRequest) -> SceneContextResponse:
    """Erzeugt einen NPC-spezifischen Szenenkontext aus einer Textgrundlage."""

    return SceneContextResponse(context=NpcSceneService().generate_context(request.content))


@router.put("/api/session/context", summary="Szenenkontext speichern")
def scene_context_update(request: SceneContextRequest) -> StateResponse:
    """Speichert den NPC-spezifischen Kontext der aktiven Szene."""

    NpcSceneService().save_active_context(request.content)
    return _state_response()


@router.get("/api/session/history", summary="Checkpoints auflisten")
def history_checkpoints() -> CheckpointListResponse:
    """Liefert alle verfügbaren Checkpoints mit Metadaten."""

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
    """Speichert den aktuellen Zustand als Checkpoint."""

    history_api.create()
    return OperationResponse(success=True)


@router.post("/api/session/history/{commit_hash}/restore", summary="Checkpoint wiederherstellen")
def history_restore_checkpoint(commit_hash: CommitHash) -> OperationResponse:
    """Stellt den Zustand aus einem gespeicherten Checkpoint wieder her."""

    history_api.restore(commit_hash)
    return OperationResponse(success=True)


@router.get("/api/session/image", summary="Aktives Laufzeitbild laden")
def image_current() -> Response:
    """Liefert das aktive Laufzeitbild des aktuellen NPC-Szenen-Kontexts als WebP."""

    return _webp_response(storage.npc.img.get())


@router.get("/api/session/image/backups", summary="Bild-Backups auflisten")
def image_current_backups() -> list[ImageBackupResponse]:
    """Liefert die Backups des aktiven Laufzeitbildes."""

    return [
        ImageBackupResponse(
            name=image.name,
            url=f"/api/session/image/backups/{image.name}?v={url_version(image.get())}",
            signature=_file_signature(image.get()),
        )
        for image in storage.npc.img_backup
    ]


@router.get("/api/session/image/backups/{backup_name}", summary="Bild-Backup laden")
def image_current_backup(backup_name: str) -> Response:
    """Liefert ein Backup des aktiven Laufzeitbildes als WebP."""

    if not is_image_backup_name(backup_name):
        raise HTTPException(status_code=404, detail="Backup-Bild nicht gefunden.")
    backup_image = next((img for img in storage.npc.img_backup if img.name == backup_name), None)
    if backup_image is None:
        raise HTTPException(status_code=404, detail="Backup-Bild nicht gefunden.")
    return _webp_response(backup_image.get())


@router.delete("/api/session/image", summary="Aktives Laufzeitbild löschen, Initialbild verwenden")
def image_current_delete() -> Response:
    """Löscht das aktive Laufzeitbild, sodass wieder das Initialbild als Standard verwendet wird; historische Bilder werden nicht gelöscht."""

    ImageService().delete_current()
    return Response(status_code=200)


@router.post("/api/session/image/refresh", summary="Aktives Laufzeitbild aktualisieren")
def image_current_refresh() -> EmptyResponse:
    """Aktualisiert das aktive Laufzeitbild aus dem aktuellen NPC-Szenen-Kontext."""

    ImageService().update_from_context(force=True)
    return EmptyResponse()


@router.post("/api/session/image/revert", summary="Auf letztes Backup zurücksetzen")
def image_current_revert() -> EmptyResponse:
    """Setzt das aktive Laufzeitbild auf das letzte verfügbare Backup zurück."""

    ImageService().revert()
    return EmptyResponse()


@router.get("/api/session/image/signature", summary="Bildsignatur abrufen")
def image_current_signature() -> ImageSignatureResponse:
    """Liefert Signatur und Metadaten des aktiven Bildzustands."""

    npc = storage.npc
    return ImageSignatureResponse(
        signature=_file_signature(npc.img.get()),
        image_is_original=npc.is_image_original,
    )


@router.put("/api/session/user-profile", summary="Nutzerprofil speichern")
def update_user_profile(request: UserProfileRequest) -> StateResponse:
    """Speichert das Laufzeit-Nutzerprofil und liefert den aktuellen App-State."""

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
    return StateResponse(
        npc=npc.npc_id,
        scene=scene.scene_id,
        scene_context=scene.npc_context.original.get(),
        messages=[MessageResponse(**message) for message in visible_messages(npc, scene)],
        messages_signature=messages_signature(npc),
        image_signature=_file_signature(npc.img.get()),
        user_profile=npc.user_profile,
        image_autogenerate=storage.session.image_autogenerate,
        default_npc=config.DEFAULT_NPC_ID,
        default_scene=config.DEFAULT_SCENE_ID,
        can_reset_scene=SceneService.can_reset_active_scene(),
    )
