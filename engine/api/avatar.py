from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import Field

from engine.api.models import ApiModel, DATA_URL_MAX_LENGTH, LONG_TEXT_MAX_LENGTH
from engine.api.state_app import EntityId
from engine.services.avatar_service import AvatarService
from engine.services.image_codec import cached_webp_bytes, normalize_image_data_url, png_data_url
from engine.storage import storage
from engine.storage.paths import path_resolver

router = APIRouter(tags=["avatar"])


class AvatarResponse(ApiModel):
    id: str = Field(description="Technische Avatar-ID, die in der Session verwendet wird.")
    name: str = Field(description="Anzeigename des Avatars aus den gespeicherten Charakterdaten.")
    description: str = Field(description="Avatar-Beschreibung als Markdown.")
    is_dynamic_avatar: bool = Field(description="Gibt an, ob der Avatar selbst erstellt wurde.")
    can_reset_avatar: bool = Field(description="Gibt an, ob der Avatar auf den mitgelieferten Stand zurückgesetzt werden kann.")


class AvatarCreateRequest(ApiModel):
    description: str = Field(
        min_length=1,
        max_length=LONG_TEXT_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Charakterbeschreibung als Markdown, aus der ein neuer Avatar erstellt wird.",
    )
    image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales fertiges Avatar-Bild als Data-URL; wird direkt gespeichert und hat Vorrang vor dem Referenzbild.",
    )
    reference_image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales Referenzbild als Data-URL; wird nur genutzt, wenn kein fertiges Avatar-Bild übergeben wurde.",
    )


class AvatarUpdateRequest(ApiModel):
    description: str = Field(
        min_length=1,
        max_length=LONG_TEXT_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Avatar-Beschreibung, die die bisherige Beschreibung ersetzt.",
    )
    image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales neues Avatar-Bild als Data-URL; fehlt es, bleibt das aktuelle Bild erhalten.",
    )


class AvatarReferenceDescriptionResponse(ApiModel):
    description: str = Field(description="Aus dem Avatar-Bild abgeleitete, editierbare Charakterbeschreibung.")


class AvatarDescribeReferenceRequest(ApiModel):
    image_data_url: str = Field(
        max_length=DATA_URL_MAX_LENGTH,
        description="Avatar-Bild als Data-URL; muss dekodierbare Bilddaten enthalten.",
    )


class AvatarPreviewImageRequest(ApiModel):
    description: str = Field(
        min_length=1,
        max_length=LONG_TEXT_MAX_LENGTH,
        pattern=r".*\S.*",
        description="Nicht leere Avatar-Beschreibung für das temporäre Vorschaubild.",
    )
    reference_image_data_url: str | None = Field(
        default=None,
        max_length=DATA_URL_MAX_LENGTH,
        description="Optionales Referenzbild als visuelle Grundlage der Bildgenerierung.",
    )


class ImageDataResponse(ApiModel):
    image_data_url: str = Field(description="Generiertes PNG-Bild als Data-URL zur direkten Vorschau oder Speicherung.")


def _avatar_create_image(avatar_service: AvatarService, character_description: str, request: AvatarCreateRequest) -> bytes | None:
    if request.image_data_url is not None:
        return normalize_image_data_url(request.image_data_url)
    if request.reference_image_data_url is None:
        return None
    reference_image = normalize_image_data_url(request.reference_image_data_url)
    return avatar_service.create_preview_image(character_description, reference_image)


def _require_avatar(avatar: EntityId) -> None:
    if not path_resolver.avatar_exists(avatar):
        raise HTTPException(status_code=404, detail="Avatar nicht gefunden.")


def _map_avatar_response(avatar_view) -> AvatarResponse:
    character = avatar_view.character.get()
    return AvatarResponse(
        id=avatar_view.avatar_id,
        name=str(character.get("name", "")).strip() or avatar_view.avatar_id,
        description=avatar_view.description.get(),
        is_dynamic_avatar=avatar_view.is_dynamic_avatar,
        can_reset_avatar=AvatarService.can_reset_avatar(avatar_view.avatar_id),
    )


@router.get("/api/avatars", summary="Avatar-Optionen laden")
def list_options() -> list[AvatarResponse]:
    """Liefert alle Avatare, die in der Oberfläche gewählt werden können, nach Anzeigename sortiert."""

    avatars = [_map_avatar_response(avatar_view) for avatar_view in storage.list_avatars]
    return sorted(avatars, key=lambda avatar: avatar.name.casefold())


@router.post("/api/avatars", summary="Avatar erstellen")
def create(request: AvatarCreateRequest) -> AvatarResponse:
    """Erstellt aus einer nicht leeren Markdown-Beschreibung einen neuen Avatar und macht ihn zum aktiven Avatar."""

    avatar_service = AvatarService()
    avatar_image = _avatar_create_image(avatar_service, request.description, request)
    target_dir = avatar_service.create_override(request.description, avatar_image)
    storage.session.avatar_id = target_dir.name
    return _map_avatar_response(storage.avatar_view(target_dir.name))


@router.get("/api/avatars/{avatar}", summary="Avatar laden")
def get_avatar(avatar: EntityId) -> AvatarResponse:
    """Liefert Anzeigename, Markdown-Beschreibung und Änderbarkeit eines Avatars."""

    _require_avatar(avatar)
    return _map_avatar_response(storage.avatar_view(avatar))


@router.put("/api/avatars/{avatar}", summary="Avatar speichern")
def update(avatar: EntityId, request: AvatarUpdateRequest) -> AvatarResponse:
    """Speichert Beschreibung und optional neues Bild eines Avatars in der Override-Ebene."""

    _require_avatar(avatar)
    image_bytes = normalize_image_data_url(request.image_data_url) if request.image_data_url is not None else None
    AvatarService().update_avatar(avatar, request.description, image_bytes)
    return _map_avatar_response(storage.avatar_view(avatar))


@router.delete("/api/avatars/{avatar}", summary="Erstellten Avatar löschen")
def delete(avatar: EntityId) -> Response:
    """Löscht einen selbst erstellten Avatar vollständig. Standard-Avatare können nicht gelöscht werden."""

    _require_avatar(avatar)
    try:
        AvatarService.delete_dynamic_avatar_artifacts(avatar)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(status_code=200)


@router.delete("/api/avatars/{avatar}/reset", summary="Avatar zurücksetzen")
def reset_active(avatar: EntityId) -> Response:
    """Setzt einen mitgelieferten Avatar auf seinen initialen Stand zurück, indem lokale Avatar-Overrides entfernt werden."""

    _require_avatar(avatar)
    try:
        AvatarService.reset_avatar_artifacts(avatar)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(status_code=200)


@router.get("/api/avatars/{avatar}/image", summary="Avatar-Bild laden")
def image(avatar: EntityId) -> Response:
    """Liefert das Avatar-Bild als WebP mit maximal 256 Pixel Breite."""

    _require_avatar(avatar)
    return Response(content=cached_webp_bytes(storage.avatar_view(avatar).img.get(), max_width=256), media_type="image/webp")


@router.post("/api/avatars/image/describe", summary="Avatar-Bild beschreiben")
def describe_image(request: AvatarDescribeReferenceRequest) -> AvatarReferenceDescriptionResponse:
    """Analysiert ein Avatar-Bild und erzeugt daraus eine editierbare Charakterbeschreibung."""

    reference_image = normalize_image_data_url(request.image_data_url)
    return AvatarReferenceDescriptionResponse(description=AvatarService().describe_reference_image(reference_image))


@router.post("/api/avatars/image/preview", summary="Avatar-Vorschaubild generieren")
def preview_image(request: AvatarPreviewImageRequest) -> ImageDataResponse:
    """Erzeugt ein temporäres Avatar-Vorschaubild aus Beschreibung und optionalem Referenzbild."""

    reference_image = None
    if request.reference_image_data_url is not None:
        reference_image = normalize_image_data_url(request.reference_image_data_url)
    image_bytes = AvatarService().create_preview_image(request.description, reference_image)
    return ImageDataResponse(image_data_url=png_data_url(image_bytes))
