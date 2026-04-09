from __future__ import annotations

import json
import shutil
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Any, AsyncIterator

import markdown
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
import uvicorn

from engine.config import config
from engine.fs_utils import load_text, load_yaml
from engine.llm_client import stream_prompt
from engine.logging import get_logger
from engine.models import Npc, ShortMemoryMessage
from engine.services.npc_turn_service import NpcTurnService
from engine.stores.npc_store import NpcStore
from engine.stores.session_store import SessionStore
from engine.updater.image_updater import ImageUpdater
from engine.updater.schedule import start_scheduler, stop_scheduler

STATIC_DIR = Path(__file__).resolve().parent / "static"

_webp_cache: dict[str, Any] = {"signature": "", "data": b""}
logger = get_logger("web")


def _problem_response(status_code: int, detail: Any) -> Response:
    return Response(
        content=json.dumps({"type": "about:blank", "status": status_code, "detail": detail}),
        status_code=status_code,
        media_type="application/problem+json",
    )


def _get_cached_webp(img_path: Path) -> bytes:
    stat = img_path.stat()
    sig = f"{stat.st_mtime_ns}|{stat.st_size}"
    if _webp_cache["signature"] == sig:
        return _webp_cache["data"]
    buf = BytesIO()
    Image.open(img_path).save(buf, format="WEBP", quality=82, method=4)
    _webp_cache["signature"] = sig
    _webp_cache["data"] = buf.getvalue()
    return _webp_cache["data"]


def _start_watchers_for_web() -> None:
    if app.state.watch_scheduler is not None:
        return
    scheduler, _ = start_scheduler(run_immediately=True)
    app.state.watch_scheduler = scheduler


def _stop_watchers_for_web() -> None:
    stop_scheduler(app.state.watch_scheduler)
    app.state.watch_scheduler = None


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _start_watchers_for_web()
    try:
        yield
    finally:
        _stop_watchers_for_web()


app = FastAPI(title="Social Game Web GUI", lifespan=_lifespan)
app.state.watch_scheduler = None


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
    "frame-ancestors 'none'; "
    "require-trusted-types-for 'script'; "
    "trusted-types sg default"
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

    if not request.url.path.startswith(("/css/", "/js/", "/icons/")):
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


@app.exception_handler(Exception)
async def _internal_error_handler(request: Request, exc: Exception) -> Response:
    logger.exception(
        "Unerwarteter Fehler in Web-Request",
        extra={"path": request.url.path, "method": request.method},
    )
    return _problem_response(500, "Interner Serverfehler.")


class ChatRequest(BaseModel):
    message: str


class SessionRequest(BaseModel):
    npc_id: str | None = None
    scene_id: str | None = None


def _message_to_payload(message: ShortMemoryMessage) -> dict[str, str]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp_utc,
    }


def _render_markdown_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["extra", "sane_lists"])


def _visible_messages(npc: Npc) -> list[dict[str, Any]]:
    visible = [_message_to_payload(m) for m in npc.stm if m.role in {"user", "assistant"}]
    if visible:
        return visible
    character_description = npc.description
    scene_description = (npc.scene.description or "").strip() or "Keine Szenenbeschreibung verfügbar."
    context_messages = [
        {
            "id": "context-character",
            "role": "assistant",
            "content": "",
            "html": _render_markdown_to_html(character_description),
            "timestamp": ""
        },
        {
            "id": "context-scene",
            "role": "assistant",
            "content": "",
            "html": _render_markdown_to_html(scene_description),
            "timestamp": ""
        },
    ]

    if npc.ltm.strip():
        context_messages.append(
            {
                "id": "context-ltm",
                "role": "assistant",
                "content": "",
                "html": _render_markdown_to_html(f"# Beziehung\n\n{npc.ltm}"),
                "timestamp": "",
            }
        )

    return context_messages


def _visible_stm_messages(npc: Npc) -> list[ShortMemoryMessage]:
    return [m for m in npc.stm if m.role in {"user", "assistant"}]


def _messages_signature(npc: Npc) -> str:
    visible = _visible_stm_messages(npc)
    last_id = visible[-1].id if visible else ""
    return f"{len(visible)}|{last_id}"


def _read_scene_label(scene_dir: Path) -> str:
    for line in load_text(scene_dir / "scene.md").splitlines():
        if (stripped := line.strip()).startswith("#"):
            return stripped.lstrip("#").strip() or scene_dir.name
    return scene_dir.name.replace("_", " ").title()


def _list_npcs() -> list[dict[str, str]]:
    if not config.NPC_DIR.exists():
        return []
    return [
        {"id": d.name, "label": str(load_yaml(d / "character.yaml").get("name", d.name)).strip() or d.name}
        for d in sorted(config.NPC_DIR.iterdir(), key=lambda p: p.name) if d.is_dir()
    ]


def _list_scenes() -> list[dict[str, str]]:
    if not config.SCENE_DIR.exists():
        return []
    return [
        {"id": d.name, "label": _read_scene_label(d)}
        for d in sorted(config.SCENE_DIR.iterdir(), key=lambda p: p.name) if d.is_dir()
    ]


def _image_url(npc: Npc) -> str | None:
    return "/api/image/current" if npc.img_current.is_file() else None


def _image_signature(npc: Npc) -> str:
    if not npc.img_current.exists():
        return ""
    stat = npc.img_current.stat()
    return f"{stat.st_mtime_ns}|{stat.st_size}"


def _state_payload() -> dict[str, Any]:
    npc = NpcStore().load()
    return {
        "npc_id": npc.npc_id,
        "npc_name": str(npc.character.get("name", npc.npc_id)).strip() or npc.npc_id,
        "character_description": npc.description,
        "ltm": npc.ltm,
        "scene_id": npc.scene.scene_id,
        "scene_description": npc.scene.description,
        "character_data": npc.character,
        "messages": _visible_messages(npc),
        "messages_signature": _messages_signature(npc),
        "image_url": _image_url(npc),
        "image_signature": _image_signature(npc),
        "npcs": _list_npcs(),
        "scenes": _list_scenes(),
    }


@app.get("/api/state")
def get_state() -> dict[str, Any]:
    return _state_payload()


@app.put("/api/session")
def update_session(request: SessionRequest) -> dict[str, Any]:
    if request.npc_id is None and request.scene_id is None:
        raise HTTPException(status_code=400, detail="Mindestens npc_id oder scene_id muss gesetzt sein.")
    try:
        SessionStore().save(npc=request.npc_id, scene=request.scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _state_payload()


@app.delete("/api/npc/reset-active")
def reset_active_npc_runtime_data() -> dict[str, Any]:
    session = SessionStore().load()
    scene_data_dir = config.DATA_NPC_DIR / session.npc_id / session.scene_id
    if scene_data_dir.exists():
        if not scene_data_dir.is_dir():
            raise HTTPException(status_code=500, detail="NPC-Scene-Datenpfad ist kein Verzeichnis.")
        try:
            shutil.rmtree(scene_data_dir)
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"NPC-Scene-Daten konnten nicht gelöscht werden: {exc}") from exc
    return _state_payload()


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest) -> Any:
    message_text = request.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Nachricht darf nicht leer sein.")

    npc_turn = NpcTurnService()
    user_message = npc_turn.build_user_message(message_text)
    turn_messages = [*npc_turn.build_turn_messages(), user_message]
    prompt_stream = stream_prompt(turn_messages)

    def event_stream():
        parts: list[str] = []
        for part in prompt_stream:
            parts.append(part)
            yield part

        reply = "".join(parts).strip()
        npc_turn.npc_store.append_stm_turn(str(user_message["content"]), reply)
        ImageUpdater().emit_update_if_missing()

    return StreamingResponse(event_stream(), media_type="text/plain; charset=utf-8")


@app.get("/api/image/current")
def current_image() -> Any:
    npc = NpcStore().load()
    if not npc.img_current.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "Kein NPC-Bild verfügbar. "
                f"npc_id='{npc.npc_id}', scene_id='{npc.scene.scene_id}', path='{npc.img_current}'"
            ),
        )
    return Response(content=_get_cached_webp(npc.img_current), media_type="image/webp")


@app.get("/api/image/signature")
def image_signature() -> dict[str, Any]:
    npc = NpcStore().load()
    return {
        "signature": _image_signature(npc),
        "image_url": _image_url(npc),
    }


@app.post("/api/image/refresh-active")
def refresh_active_image() -> dict[str, Any]:
    updater = ImageUpdater()
    updater.emit_update()
    updater.schedule(force=True)
    return {}


def run(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    uvicorn.run("engine.web.app:app", host=host, port=port, reload=reload)


# Montiere statische Dateien am Ende, damit API-Routes zuerst geprueft werden.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
