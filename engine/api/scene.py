from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import Field

from engine.api.models import ApiModel, DATA_URL_MAX_LENGTH, LONG_TEXT_MAX_LENGTH
from engine.api.state_npc import render_markdown_to_html
from engine.api.state_app import EntityId
from engine.services.image_codec import cached_webp_bytes, normalize_image_data_url, png_data_url
from engine.services.npc_scene_service import NpcSceneService
from engine.services.scene_service import SceneService
from engine.storage import storage
from engine.tools.scheduler import get_scheduler as _get_scheduler

get_scheduler = _get_scheduler

router = APIRouter(tags=["scene"])


def _webp_response(image_path, max_width: int | None = None) -> Response:
    return Response(content=cached_webp_bytes(image_path, max_width=max_width), media_type="image/webp")


def _read_scene_label(scene_id: str, location_markdown: str) -> str:
    for line in location_markdown.splitlines():
        if (stripped := line.strip()).startswith("#"):
            return stripped.lstrip("#").strip() or scene_id
    return scene_id.replace("_", " ").title()


def _scene_option_image_path(scene: EntityId):
    npc_id = storage.session.npc_id
    return storage.scene_view(scene_id=scene, npc_id=npc_id).location.img_original.get()


class SceneResponse(ApiModel):
    id: str = Field(description="Technische Szenen-ID, die in Session- und Pfadparametern verwendet wird.")
    name: str = Field(description="Anzeigename der Szene; wird aus der ersten Markdown-Überschrift oder aus der ID abgeleitet.")
    description_html: str = Field(description="Gerenderte HTML-Fassung der Szenenbeschreibung für die Oberfläche.")
    description: str = Field(description="Szenenbeschreibung als Markdown.")
    is_dynamic_scene: bool = Field(description="Gibt an, ob die Szene selbst erstellt wurde.")


def _map_scene_response(scene_view) -> SceneResponse:
    location_original = scene_view.location.original.get()
    return SceneResponse(
        id=scene_view.scene_id,
        name=_read_scene_label(scene_view.scene_id, location_original),
        description_html=render_markdown_to_html(location_original),
        description=location_original,
        is_dynamic_scene=scene_view.location.is_dynamic,
    )


class SceneCreateRequest(ApiModel):
    description: str = Field(
        min_length=1,
        max_length=LONG_TEXT_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Szenenbeschreibung als Markdown, aus der eine neue Szene erstellt wird.",
    )
    image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales fertiges Szenenbild als Data-URL; wird direkt gespeichert und hat Vorrang vor dem Referenzbild.",
    )
    reference_image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales Referenzbild als Data-URL; wird nur genutzt, wenn kein fertiges Szenenbild übergeben wurde.",
    )


class SceneDescriptionResponse(ApiModel):
    description: str = Field(description="Aus dem Referenzbild abgeleitete, editierbare Beschreibung der sichtbaren Location.")


class SceneReferenceImageRequest(ApiModel):
    image_data_url: str = Field(
        max_length=DATA_URL_MAX_LENGTH,
        description="Referenzbild der Location als Data-URL; muss dekodierbare Bilddaten enthalten.",
    )


class ScenePreviewImageRequest(ApiModel):
    description: str = Field(
        min_length=1,
        max_length=LONG_TEXT_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Szenenbeschreibung für das temporäre Vorschaubild.",
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


@router.get("/api/scenes", summary="Szenen-Optionen laden")
def list_options() -> list[SceneResponse]:
    """Liefert alle Szenen, die in der Oberfläche gewählt werden können. Jeder Eintrag enthält ID, Anzeigename, Markdown-Beschreibung, HTML-Beschreibung und die Information, ob die Szene selbst erstellt wurde."""

    return [_map_scene_response(scene_view) for scene_view in storage.list_scenes]


@router.get("/api/scenes/{scene}", summary="Szene laden")
def get_scene(scene: EntityId) -> SceneResponse:
    """Liefert Anzeigename, Markdown-Beschreibung und HTML-Beschreibung einer Szene. Die Szenen-ID muss dem technischen ID-Format entsprechen und vorhanden sein."""

    scene_view = storage.scene_view(scene_id=scene)
    return _map_scene_response(scene_view)


@router.post("/api/scenes", summary="Szene erstellen")
def create(request: SceneCreateRequest) -> SceneResponse:
    """Erstellt aus einer nicht leeren Markdown-Beschreibung eine neue Szene und macht sie zur aktiven Szene. Wenn `imageDataUrl` gesetzt ist, wird dieses Bild verwendet; sonst kann aus `referenceImageDataUrl` automatisch ein Bild erzeugt werden."""

    scene_description = request.description

    scene_service = SceneService()
    scene_image = _scene_create_image(scene_service, scene_description, request)
    scene_dir = scene_service.create_override(scene_description, scene_image)
    storage.session.scene_id = scene_dir.name

    NpcSceneService().create_override(scene_description)
    NpcSceneService().adapt_default_fallback()
    if storage.session.image_autogenerate:
        get_scheduler().enqueue("image")
    scene_view = storage.scene_view(scene_id=scene_dir.name, npc_id=storage.session.npc_id)

    return _map_scene_response(scene_view)


@router.delete("/api/scenes/{scene}", summary="Erstellte Szene löschen")
def delete(scene: EntityId) -> Response:
    """Entfernt eine selbst erstellte Szene. Bei mitgelieferten Szenen bleiben die Grunddaten erhalten; zurücksetzbare Nutzerdaten werden gelöscht."""

    get_scheduler().clear_pending_jobs()
    scene_view = storage.scene_view(scene_id=scene)
    if scene_view.location.is_dynamic:
        SceneService.delete_dynamic_scene(scene)
    else:
        SceneService.reset_scene_artifacts(scene)
    return Response(status_code=200)


@router.get("/api/scenes/{scene}/image", summary="Szenen-Vorschaubild laden")
def option_image(scene: EntityId) -> Response:
    """Liefert das Vorschaubild einer Szene als WebP mit maximal 256 Pixel Breite."""

    return _webp_response(_scene_option_image_path(scene=scene), max_width=256)


@router.put("/api/scenes/{scene}", summary="Szene speichern")
def update(scene: EntityId, request: SceneCreateRequest) -> OperationResponse:
    """Speichert Beschreibung und Bild für die angegebene Szene und macht sie zur aktiven Szene. Wenn automatische Bildgenerierung aktiv ist, wird das Szenenbild anschließend aktualisiert."""

    storage.session.scene_id = scene
    scene_description = request.description
    scene_service = SceneService()
    scene_image = _scene_create_image(scene_service, scene_description, request)
    scene_service.update_active_override(scene_description, scene_image)
    NpcSceneService().create_override(scene_description)
    if storage.session.image_autogenerate:
        get_scheduler().enqueue("image")
    return OperationResponse(success=True)


@router.delete("/api/scenes/{scene}/reset", summary="Szene zurücksetzen")
def reset_active(scene: EntityId) -> Response:
    """Setzt zurücksetzbare Nutzerdaten der angegebenen Szene zurück, einschließlich Dialogen, Szenenkontexten und Bildern."""

    get_scheduler().clear_pending_jobs()
    SceneService.reset_active_scene_artifacts(scene)
    return Response(status_code=200)


def _scene_create_image(scene_service: SceneService, scene_description: str, request: SceneCreateRequest) -> bytes | None:
    image_bytes = None
    if request.image_data_url is not None:
        image_bytes = normalize_image_data_url(request.image_data_url)
    reference_image_bytes = None
    if request.reference_image_data_url is not None:
        reference_image_bytes = normalize_image_data_url(request.reference_image_data_url)
    return scene_service.resolve_create_image(scene_description, image_bytes, reference_image_bytes)


@router.post("/api/scenes/image/describe", summary="Referenzbild beschreiben")
def describe_image(request: SceneReferenceImageRequest) -> SceneDescriptionResponse:
    """Analysiert ein Referenzbild und liefert eine editierbare Beschreibung der sichtbaren Location. Der Request muss eine dekodierbare Bild-Data-URL enthalten."""

    reference_image = normalize_image_data_url(request.image_data_url)
    return SceneDescriptionResponse(description=SceneService().describe_reference_image(reference_image))


@router.post("/api/scenes/image/preview", summary="Vorschaubild erzeugen")
def preview_image(request: ScenePreviewImageRequest) -> ImageDataResponse:
    """Erzeugt ein temporäres Szenenbild aus einer nicht leeren Beschreibung und optionaler visueller Referenz. Das Bild wird als PNG-Data-URL zurückgegeben und nicht automatisch gespeichert."""

    scene_description = request.description
    reference_image = None
    if request.reference_image_data_url is not None:
        reference_image = normalize_image_data_url(request.reference_image_data_url)
    image_bytes = SceneService().create_preview_image(scene_description, reference_image)
    return ImageDataResponse(image_data_url=png_data_url(image_bytes))
