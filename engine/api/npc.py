from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import Field

from engine.api.models import ApiModel, DATA_URL_MAX_LENGTH, LONG_TEXT_MAX_LENGTH
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
    id: str = Field(description="Technische NPC-ID, die in Session- und Pfadparametern verwendet wird.")
    name: str = Field(description="Anzeigename des NPC aus den gespeicherten Charakterdaten.")
    description: str = Field(description="Charakterbeschreibung als Markdown.")
    has_video: bool = Field(description="Gibt an, ob für diesen NPC ein MP4-Video vorhanden ist.")
    is_dynamic_npc: bool = Field(description="Gibt an, ob der NPC selbst erstellt wurde.")


class NpcCreateRequest(ApiModel):
    description: str = Field(
        min_length=1,
        max_length=LONG_TEXT_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Charakterbeschreibung als Markdown, aus der ein neuer NPC erstellt wird.",
    )
    image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales fertiges NPC-Bild als Data-URL; wird direkt gespeichert und hat Vorrang vor dem Referenzbild.",
    )
    reference_image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales Referenzbild als Data-URL; wird nur genutzt, wenn kein fertiges NPC-Bild übergeben wurde.",
    )


class NpcReferenceDescriptionResponse(ApiModel):
    description: str = Field(description="Aus dem Referenzbild abgeleitete, editierbare Charakterbeschreibung.")


class NpcDescribeReferenceRequest(ApiModel):
    image_data_url: str = Field(
        max_length=DATA_URL_MAX_LENGTH,
        description="Referenzbild als Data-URL; muss dekodierbare Bilddaten enthalten.",
    )


class NpcPreviewImageRequest(ApiModel):
    description: str = Field(
        min_length=1,
        max_length=LONG_TEXT_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Charakterbeschreibung für das temporäre Vorschaubild.",
    )
    reference_image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales Referenzbild als visuelle Grundlage der Bildgenerierung.",
    )


class ImageDataResponse(ApiModel):
    image_data_url: str = Field(description="Generiertes PNG-Bild als Data-URL zur direkten Vorschau oder Speicherung.")


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
        has_video=npc_view.video.is_file(),
        is_dynamic_npc=npc_view.is_dynamic_npc,
    )


@router.get("/api/npcs", summary="NPC-Optionen laden")
def list_options() -> list[NpcResponse]:
    """Liefert alle NPCs, die in der Oberfläche gewählt werden können. Jeder Eintrag enthält ID, Anzeigename, Markdown-Beschreibung sowie Angaben zu Video und selbst erstellten NPCs."""

    return [_map_npc_response(npc_view) for npc_view in storage.list_npcs]


index = list_options


@router.post("/api/npcs", summary="NPC erstellen")
def create(request: NpcCreateRequest) -> NpcResponse:
    """Erstellt aus einer nicht leeren Markdown-Beschreibung einen neuen NPC und macht ihn zum aktiven NPC. Wenn `imageDataUrl` gesetzt ist, wird dieses Bild verwendet; sonst kann aus `referenceImageDataUrl` automatisch ein Bild generiert werden."""

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
    """Liefert Anzeigename, Markdown-Beschreibung und Medienhinweise eines NPCs. Die NPC-ID muss dem technischen ID-Format entsprechen und vorhanden sein."""

    npc_view = storage.npc_view(npc_id=npc)
    return _map_npc_response(npc_view)


@router.delete("/api/npcs/{npc}", summary="Erstellten NPC löschen")
def delete(npc: EntityId) -> Response:
    """Entfernt einen selbst erstellten NPC. Bei mitgelieferten NPCs bleiben die Grunddaten erhalten; zurücksetzbare Nutzerdaten werden gelöscht."""

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
    """Liefert das Vorschaubild eines NPCs als WebP mit maximal 256 Pixel Breite."""

    return _webp_response(_npc_option_image_path(npc=npc), max_width=256)


@router.delete("/api/npcs/{npc}/reset", summary="NPC zurücksetzen")
def reset_active(npc: EntityId) -> Response:
    """Setzt zurücksetzbare Nutzerdaten des angegebenen NPCs zurück, einschließlich Dialogen und Szenenkontexten."""

    get_scheduler().clear_pending_jobs()
    NpcService.reset_npc_artifacts(npc)
    return Response(status_code=200)


@router.get("/api/npcs/{npc}/video", summary="NPC-Video laden")
def video(npc: EntityId) -> FileResponse:
    """Liefert das MP4-Video eines NPCs. Wenn für die angefragte NPC-ID kein Video existiert, antwortet die API mit 404."""

    video = _npc_option_video(npc=npc)
    if not video.is_file():
        raise HTTPException(status_code=404, detail="NPC-Video nicht gefunden.")
    return FileResponse(video.get(), media_type="video/mp4")


@router.post("/api/npcs/image/describe", summary="NPC-Bild beschreiben")
def describe_image(request: NpcDescribeReferenceRequest) -> NpcReferenceDescriptionResponse:
    """Analysiert ein Referenzbild und erzeugt daraus eine editierbare Charakterbeschreibung. Der Request muss eine dekodierbare Bild-Data-URL enthalten."""

    reference_image = normalize_image_data_url(request.image_data_url)
    return NpcReferenceDescriptionResponse(description=NpcService().describe_reference_image(reference_image))


@router.post("/api/npcs/image/preview", summary="NPC-Vorschaubild generieren")
def preview_image(request: NpcPreviewImageRequest) -> ImageDataResponse:
    """Erzeugt ein temporäres NPC-Vorschaubild aus einer nicht leeren Charakterbeschreibung und optionalem Referenzbild. Das Bild wird als PNG-Data-URL zurückgegeben und nicht automatisch gespeichert."""

    character_description = request.description
    reference_image = None
    if request.reference_image_data_url is not None:
        reference_image = normalize_image_data_url(request.reference_image_data_url)
    image_bytes = NpcService().create_preview_image(character_description, reference_image)
    return ImageDataResponse(image_data_url=png_data_url(image_bytes))
