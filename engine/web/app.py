from __future__ import annotations

import json
import shutil
from contextlib import asynccontextmanager
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncIterator

import markdown
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
import uvicorn

from engine.config import config
from engine.client import client, user_visible_provider_error_detail
from engine.services.image_service import ImageService
from engine.services.npc_turn_service import NpcTurnService
from engine.storage import storage
from engine.storage.models import Message
from engine.tools.scheduler import Scheduler

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_ASSET_PREFIXES = ("/css/", "/js/", "/icons/")
VISIBLE_CHAT_ROLES = {"user", "assistant"}

_webp_cache: dict[str, dict[str, Any]] = {}
_scheduler: Scheduler | None = None


def _get_scheduler() -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def _problem_response(status_code: int, detail: Any) -> Response:
    return Response(
        content=json.dumps({"type": "about:blank", "status": status_code, "detail": detail}),
        status_code=status_code,
        media_type="application/problem+json",
    )


def _stream_event(event_type: str, **payload: Any) -> str:
    return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"


def _stream_error_event(exc: Exception) -> str:
    detail = user_visible_provider_error_detail(exc) or "Interner Serverfehler."
    return _stream_event("error", detail=detail)


def _get_cached_webp(img_path: Path, max_width: int | None = None) -> bytes:
    stat = img_path.stat()
    sig = f"{stat.st_mtime_ns}|{stat.st_size}"
    width_key = "orig" if max_width is None else str(max_width)
    cache_key = f"{img_path}|{width_key}"
    cached = _webp_cache.get(cache_key)
    if cached and cached["signature"] == sig:
        return cached["data"]

    buf = BytesIO()
    with Image.open(img_path) as image:
        if max_width is not None and image.width > max_width:
            ratio = max_width / image.width
            target_height = max(1, int(image.height * ratio))
            image = image.resize((max_width, target_height), Image.Resampling.LANCZOS)
        image.save(buf, format="WEBP", quality=82, method=4)

    _webp_cache[cache_key] = {"signature": sig, "data": buf.getvalue()}
    return _webp_cache[cache_key]["data"]


def _file_signature(path: Path) -> str:
    if not path.exists():
        return ""
    stat = path.stat()
    return f"{stat.st_mtime_ns}|{stat.st_size}"


def _url_version(path: Path) -> str:
    return _file_signature(path).replace("|", "-")


def _image_response(img_path: Path, max_width: int | None = None) -> Response:
    return Response(content=_get_cached_webp(img_path, max_width=max_width), media_type="image/webp")


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    scheduler = _get_scheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.stop()


app = FastAPI(title="Social Game", lifespan=_lifespan)


_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data: blob:; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def _add_web_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = _CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    if not request.url.path.startswith(STATIC_ASSET_PREFIXES):
        return response

    if config.WEB_DEBUG:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    else:
        response.headers["Cache-Control"] = "public, max-age=3600"

    return response


@app.exception_handler(HTTPException)
async def _problem_detail_handler(_request: Request, exc: HTTPException) -> Response:
    return _problem_response(exc.status_code, exc.detail)


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(_request: Request, exc: RequestValidationError) -> Response:
    return _problem_response(422, exc.errors())


@app.exception_handler(ValueError)
async def _value_error_handler(_request: Request, exc: ValueError) -> Response:
    return _problem_response(400, str(exc))


@app.exception_handler(Exception)
async def _internal_error_handler(_request: Request, exc: Exception) -> Response:
    detail = user_visible_provider_error_detail(exc)
    if detail is not None:
        return _problem_response(400, detail)
    return _problem_response(500, "Interner Serverfehler.")


class ChatRequest(BaseModel):
    message: str


class SessionRequest(BaseModel):
    npc_id: str | None = None
    scene_id: str | None = None


class UserProfileRequest(BaseModel):
    content: str


def _render_markdown_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["extra", "sane_lists"])


def _parse_state_meta(state_text: str) -> tuple[dict[str, Any], str]:
    parser = markdown.Markdown(extensions=["meta", "extra", "sane_lists"])
    body_html = parser.convert(state_text)
    raw_meta = getattr(parser, "Meta", {})
    meta_values: dict[str, Any] = {}
    for key, values in raw_meta.items():
        raw_value = "\n".join(values).strip() if isinstance(values, list) else str(values).strip()
        if not raw_value:
            continue
        meta_values[key] = yaml.safe_load(raw_value)
    return meta_values, body_html


def _dump_state_meta_yaml(meta_values: dict[str, Any]) -> str:
    if not meta_values:
        return ""
    return yaml.safe_dump(meta_values, sort_keys=False, allow_unicode=True).strip()


def _render_state_to_html(state_text: str) -> str:
    meta_values, body_html = _parse_state_meta(state_text)
    html_parts = [_render_markdown_to_html("# Beziehung")]
    meta_yaml = _dump_state_meta_yaml(meta_values)
    if meta_yaml:
        html_parts.append(f"<pre>{escape(meta_yaml)}</pre>")
    if body_html.strip():
        html_parts.append(body_html)
    return "\n".join(html_parts)


def _visible_messages(npc, scene) -> list[dict[str, Any]]:
    visible = [m.model_dump() for m in npc.stm.get() if m.role in VISIBLE_CHAT_ROLES]
    if visible:
        return visible
    character_description = npc.description.get()
    npc_state = npc.state.strip()
    scene_description = scene.description.strip() or "Keine Szenenbeschreibung verfügbar."
    context_messages = [
        {
            "id": "context-character",
            "role": "assistant",
            "content": "",
            "html": _render_markdown_to_html(character_description),
            "timestamp_utc": ""
        },
        {
            "id": "context-scene",
            "role": "assistant",
            "content": "",
            "html": _render_markdown_to_html(scene_description),
            "timestamp_utc": ""
        },
        {
            "id": "context-state",
            "role": "assistant",
            "content": "",
            "html": _render_state_to_html(npc_state),
            "timestamp_utc": "",
        },
    ]

    return context_messages


def _visible_stm_messages(npc) -> list[Message]:
    return [m for m in npc.stm.get() if m.role in VISIBLE_CHAT_ROLES]


def _messages_signature(npc) -> str:
    visible = _visible_stm_messages(npc)
    last_id = visible[-1].id if visible else ""
    return f"{len(visible)}|{last_id}"


def _read_scene_label(scene_view) -> str:
    scene_id = scene_view.scene_id
    scene_item = scene_view.scene_original
    for line in scene_item.get().splitlines():
        if (stripped := line.strip()).startswith("#"):
            return stripped.lstrip("#").strip() or scene_id
    return scene_id.replace("_", " ").title()


def _npc_option_image_path(npc_id: str) -> Path:
    scene_id = storage.session.scene_id
    return storage.npc_view(npc_id=npc_id, scene_id=scene_id).img_original.get()


def _scene_option_image_path(scene_id: str) -> Path:
    npc_id = storage.session.npc_id
    return storage.scene_view(npc_id=npc_id, scene_id=scene_id).img_original.get()


def _npc_option_image_url(npc_id: str) -> str:
    version = _url_version(_npc_option_image_path(npc_id=npc_id))
    return f"/api/npcs/{npc_id}/image?v={version}"


def _scene_option_image_url(scene_id: str) -> str:
    version = _url_version(_scene_option_image_path(scene_id=scene_id))
    return f"/api/scenes/{scene_id}/image?v={version}"


def _list_npcs() -> list[dict[str, str]]:
    return [
        {
            "id": npc_view.npc_id,
            "label": str(npc_view.character_original.get().get("name", npc_view.npc_id)).strip() or npc_view.npc_id,
            "image_url": _npc_option_image_url(npc_id=npc_view.npc_id),
        }
        for npc_view in storage.list_npcs
    ]


def _list_scenes() -> list[dict[str, str]]:
    return [
        {
            "id": scene_view.scene_id,
            "label": _read_scene_label(scene_view),
            "image_url": _scene_option_image_url(scene_id=scene_view.scene_id),
        }
        for scene_view in storage.list_scenes
    ]


def _image_url(npc) -> str | None:
    return "/api/image/current" if npc.img.is_file() else None


def _image_signature(npc) -> str:
    return _file_signature(npc.img.get())


def _state_payload() -> dict[str, Any]:
    npc = storage.npc
    scene = storage.scene
    character = npc.character_original.get()
    return {
        "npc_id": npc.npc_id,
        "npc_name": str(character.get("name", npc.npc_id)).strip() or npc.npc_id,
        "character_description": npc.description.get(),
        "scene_id": scene.scene_id,
        "scene_description": scene.description,
        "character_data": character,
        "messages": _visible_messages(npc, scene),
        "messages_signature": _messages_signature(npc),
        "image_url": _image_url(npc),
        "image_signature": _image_signature(npc),
        "npcs": _list_npcs(),
        "scenes": _list_scenes(),
        "user_profile": npc.user_profile,
    }


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return _state_payload()


@app.put("/api/session")
def update_session(request: SessionRequest) -> dict[str, Any]:
    if request.npc_id is None and request.scene_id is None:
        raise HTTPException(status_code=422, detail="Mindestens npc_id oder scene_id muss gesetzt sein.")
    if request.npc_id is not None:
        storage.session.npc_id = request.npc_id
    if request.scene_id is not None:
        storage.session.scene_id = request.scene_id
    return _state_payload()


@app.put("/api/user-profile")
def update_user_profile(request: UserProfileRequest) -> dict[str, Any]:
    storage.npc.user_profile_runtime.save(request.content)
    return _state_payload()


@app.delete("/api/npc/reset-active")
def reset_active_npc_runtime_data() -> dict[str, Any]:
    _get_scheduler().clear_pending_jobs()
    session = storage.session
    scene_data_dir = storage.npc_view(
        npc_id=session.npc_id,
        scene_id=session.scene_id,
    ).base_runtime
    if scene_data_dir.exists():
        shutil.rmtree(scene_data_dir)
    return _state_payload()


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest) -> Any:
    message_text = request.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Nachricht darf nicht leer sein.")

    npc_turn = NpcTurnService()
    turn_messages = npc_turn.build_chat_messages(message_text)
    prompt_stream = client.stream_prompt(turn_messages)

    def event_stream():
        parts: list[str] = []
        try:
            for part in prompt_stream:
                parts.append(part)
                yield _stream_event("chunk", delta=part)
        except Exception as exc:
            yield _stream_error_event(exc)
            return

        try:
            reply = "".join(parts).strip()
            npc_turn.finalize_turn(message_text, reply)
            _get_scheduler().enqueue_all()
            yield _stream_event("done")
        except Exception as exc:
            yield _stream_error_event(exc)

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.get("/api/image/current")
def current_image() -> Any:
    return _image_response(storage.npc.img.get())


@app.get("/api/npcs/{npc_id}/image")
def npc_option_image(npc_id: str) -> Any:
    return _image_response(_npc_option_image_path(npc_id=npc_id), max_width=100)


@app.get("/api/scenes/{scene_id}/image")
def scene_option_image(scene_id: str) -> Any:
    return _image_response(_scene_option_image_path(scene_id=scene_id), max_width=100)


@app.get("/api/image/signature")
def image_signature() -> dict[str, Any]:
    npc = storage.npc
    return {
        "signature": _image_signature(npc),
        "image_url": _image_url(npc),
    }


@app.post("/api/image/refresh-active")
def refresh_active_image() -> dict[str, Any]:
    ImageService().update_from_context(force=True)
    return {}


@app.post("/api/image/revert-active")
def revert_active_image() -> dict[str, Any]:
    ImageService().revert()
    return {}


@app.delete("/api/image/delete-active")
def delete_active_image() -> dict[str, Any]:
    ImageService().delete_current()
    return _state_payload()


def run(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    uvicorn.run("engine.web.app:app", host=host, port=port, reload=reload)


# Montiere statische Dateien am Ende, damit API-Routes zuerst geprueft werden.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
