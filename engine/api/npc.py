from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import Field

from engine.api.models import ApiModel
from engine.api.state_app import (
    EntityId,
)
from engine.services.image_codec import cached_webp_bytes, normalize_image_data_url, png_data_url
from engine.services.npc_scene_service import NpcSceneService
from engine.services.npc_service import NpcService
from engine.storage import storage
from engine.tools.scheduler import get_scheduler as _get_scheduler

get_scheduler = _get_scheduler

router = APIRouter(tags=["npc"])


class NpcResponse(ApiModel):
    id: str
    name: str
    description: str
    image_is_original: bool
    has_video: bool
    is_dynamic_npc: bool


class NpcCreateRequest(ApiModel):
    description: str = Field(min_length=1, pattern=r".*\S.*")
    image_data_url: str | None = Field(
        default=None,
        description="Optionales NPC-Bild als Data-URL.",
    )
    reference_image_data_url: str | None = Field(
        default=None,
        description="Optionales Referenzbild als Data-URL zur automatischen Bildgenerierung.",
    )


class NpcReferenceDescriptionResponse(ApiModel):
    description: str = Field(description="Editierbare Charakterbeschreibung aus dem Referenzbild.")


class NpcDescribeReferenceRequest(ApiModel):
    image_data_url: str = Field(description="Referenzbild als Data-URL.")


class NpcPreviewImageRequest(ApiModel):
    description: str = Field(min_length=1, pattern=r".*\S.*")
    reference_image_data_url: str | None = Field(
        default=None,
        description="Optionales Referenzbild als Data-URL.",
    )


class ImageDataResponse(ApiModel):
    image_data_url: str = Field(description="PNG-Bild als Data-URL.")


class OperationResponse(ApiModel):
    success: bool = Field(description="Gibt an, ob die Operation erfolgreich war.")


def _npc_create_image(npc_service: NpcService, character_description: str, request: NpcCreateRequest) -> bytes | None:
    """Bestimmt das zu verwendende NPC-Bild aus Preview- oder Referenzdaten."""

    if request.image_data_url is not None:
        return normalize_image_data_url(request.image_data_url)
    if request.reference_image_data_url is None:
        return None
    reference_image = normalize_image_data_url(request.reference_image_data_url)
    return npc_service.create_preview_image(character_description, reference_image)


def _webp_response(image_path, max_width: int | None = None) -> Response:
    return Response(content=cached_webp_bytes(image_path, max_width=max_width), media_type="image/webp")


def _npc_option_image_path(npc: EntityId):
    scene_id = storage.session.scene_id
    return storage.npc_view(npc_id=npc, scene_id=scene_id).img_original.get()


def _npc_option_video(npc: EntityId):
    scene_id = storage.session.scene_id
    return storage.npc_view(npc_id=npc, scene_id=scene_id).video


def _map_npc_response(npc_view) -> NpcResponse:
    return NpcResponse(
        id=npc_view.npc_id,
        name=str(npc_view.character.get().get("name", "")).strip(),
        description=npc_view.description.get(),
        image_is_original=npc_view.is_image_original,
        has_video=npc_view.video.is_file(),
        is_dynamic_npc=npc_view.is_dynamic_npc,
    )


@router.get("/api/npcs", summary="NPC-Optionen laden")
def list_options() -> list[NpcResponse]:
    """Liefert die auswählbaren NPC-Optionen mit Vorschaubild und optionalem Video."""

    return [_map_npc_response(npc_view) for npc_view in storage.list_npcs]


index = list_options


@router.post("/api/npcs", summary="NPC erstellen")
def create(request: NpcCreateRequest) -> NpcResponse:
    """Erstellt einen NPC-Override, aktiviert ihn in der Session und liefert die neue NPC-Option."""

    character_description = request.description
    npc_service = NpcService()
    npc_image = _npc_create_image(npc_service, character_description, request)
    target_dir = npc_service.create_override(character_description, npc_image)
    storage.session.npc_id = target_dir.name
    NpcSceneService().adapt_default_fallback()
    npc_view = storage.npc_view(npc_id=target_dir.name, scene_id=storage.session.scene_id)

    return _map_npc_response(npc_view)


@router.get("/api/npcs/{npc}", summary="NPC laden")
def get_npc(npc: EntityId) -> NpcResponse:
    """Liefert statische Eigenschaften eines NPCs für die aktuelle Szene."""

    npc_view = storage.npc_view(npc_id=npc)
    return _map_npc_response(npc_view)


@router.delete("/api/npcs/{npc}", summary="Erstellten NPC löschen")
def delete(npc: EntityId) -> Response:
    """Löscht einen erstellten NPC inklusive aller Artefakte; bei Standard-NPCs werden nur Artefakte zurückgesetzt und der NPC selbst bleibt erhalten."""

    get_scheduler().clear_pending_jobs()
    npc_view = storage.npc_view(npc_id=npc)
    if npc_view.is_dynamic_npc:
        NpcService.delete_dynamic_npc_artifacts(npc)
    else:
        NpcService.reset_npc_artifacts(npc)
    return Response(status_code=200)


@router.get("/api/npcs/{npc}/image", summary="NPC-Vorschaubild laden")
@router.get("/api/npcs/{npc}/image/original", summary="NPC-Vorschaubild laden", include_in_schema=False)
def image(npc: EntityId) -> Response:
    """Liefert das Vorschaubild eines NPCs für die Auswahl."""

    return _webp_response(_npc_option_image_path(npc=npc), max_width=256)


@router.delete("/api/npcs/{npc}/reset", summary="NPC zurücksetzen")
def reset_active(npc: EntityId) -> Response:
    """Setzt lokale Artefakte des übergebenen NPC zurück (z. B. alle Runtime-Daten und NPC-Szenenkontexte), damit nach dem Zurücksetzen keine veralteten Restdaten den Zustand oder Folgeschritte verfälschen."""

    get_scheduler().clear_pending_jobs()
    NpcService.reset_npc_artifacts(npc)
    return Response(status_code=200)


@router.get("/api/npcs/{npc}/video", summary="NPC-Video laden")
def video(npc: EntityId) -> FileResponse:
    """Liefert das NPC-Video für die Auswahl."""

    video = _npc_option_video(npc=npc)
    if not video.is_file():
        raise HTTPException(status_code=404, detail="NPC-Video nicht gefunden.")
    return FileResponse(video.get(), media_type="video/mp4")


@router.post("/api/npcs/image/describe", summary="NPC-Bild beschreiben")
def describe_image(request: NpcDescribeReferenceRequest) -> NpcReferenceDescriptionResponse:
    """Analysiert ein Referenzbild und erzeugt daraus eine Charakterbeschreibung."""

    reference_image = normalize_image_data_url(request.image_data_url)
    return NpcReferenceDescriptionResponse(description=NpcService().describe_reference_image(reference_image))


@router.post("/api/npcs/image/preview", summary="NPC-Vorschaubild generieren")
def preview_image(request: NpcPreviewImageRequest) -> ImageDataResponse:
    """Erzeugt ein Vorschau-NPC-Bild aus Charakterbeschreibung und optionalem Referenzbild."""

    character_description = request.description
    reference_image = None
    if request.reference_image_data_url is not None:
        reference_image = normalize_image_data_url(request.reference_image_data_url)
    image_bytes = NpcService().create_preview_image(character_description, reference_image)
    return ImageDataResponse(image_data_url=png_data_url(image_bytes))
