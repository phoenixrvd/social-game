from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from engine.api.error_response import ERROR_RESPONSES
from engine.config import config
from engine.client import client, user_visible_provider_error_detail
from engine.storage import storage
from engine.tools.scheduler import Scheduler, set_scheduler
from . import chat, history, npc, scene, session

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"
STATIC_ASSET_PREFIXES = ("/css/", "/js/", "/icons/", "/react/")


class SpaStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not Path(path).suffix:
                return await super().get_response("index.html", scope)
            raise
        if response.status_code != 404 or Path(path).suffix:
            return response
        return await super().get_response("index.html", scope)


def _problem_response(status_code: int, detail: Any) -> Response:
    return Response(
        content=json.dumps({"type": "about:blank", "status": status_code, "detail": detail}),
        status_code=status_code,
        media_type="application/problem+json",
    )


def generate_unique_id_function(route: APIRoute) -> str:
    if route.name.startswith("image_current"):
        return "".join(part[:1].upper() + part[1:] for part in route.name.split("_") if part).replace("Image", "image", 1)
    if route.name == "describe_image":
        suffix = "Npc" if route.path.startswith("/api/npcs/") else "Scene"
        return f"imageDescribe{suffix}"
    if route.name == "preview_image":
        suffix = "Npc" if route.path.startswith("/api/npcs/") else "Scene"
        return f"imagePreview{suffix}"
    module_name = route.endpoint.__module__.rsplit(".", 1)[-1]
    operation_suffix = "".join(part[:1].upper() + part[1:] for part in route.name.split("_") if part)
    return f"{module_name}{operation_suffix}"


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    scheduler = Scheduler()
    set_scheduler(scheduler)
    scheduler.start()
    try:
        yield
    finally:
        scheduler.stop()


app = FastAPI(
    title="Social Game",
    lifespan=_lifespan,
    responses=ERROR_RESPONSES,
    generate_unique_id_function=generate_unique_id_function,
)


@app.get("/sg", include_in_schema=False, operation_id="appSgSpaRoute")
def sg_spa_route() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data: blob:; "
    "media-src 'self'; "
    "connect-src 'self'; "
    "font-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)

_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
    "media-src 'self'; "
    "connect-src 'self'; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def _add_web_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/docs", "/redoc")):
        response.headers["Content-Security-Policy"] = _DOCS_CSP
    else:
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
    first_error = exc.errors()[0] if exc.errors() else {}
    error_ctx = first_error.get("ctx", {})
    original_error = error_ctx.get("error")
    if isinstance(original_error, Exception):
        message = str(original_error)
    else:
        message = str(first_error.get("msg", "Ungueltige Anfrage."))
    if first_error.get("type") == "string_pattern_mismatch":
        message = "Eingabe darf nicht leer sein."
    if message.startswith("Value error, "):
        message = message.removeprefix("Value error, ")
    return JSONResponse(status_code=400, content={"message": message})


@app.exception_handler(ValueError)
async def _value_error_handler(_request: Request, exc: ValueError) -> Response:
    return _problem_response(400, str(exc))


@app.exception_handler(Exception)
async def _internal_error_handler(_request: Request, exc: Exception) -> Response:
    detail = user_visible_provider_error_detail(exc)
    if detail is not None:
        return _problem_response(400, detail)
    return _problem_response(500, "Interner Serverfehler.")


app.include_router(chat.router)
app.include_router(npc.router)
app.include_router(scene.router)
app.include_router(session.router)

for route in app.routes:
    if isinstance(route, APIRoute) and route.operation_id is None:
        route.operation_id = generate_unique_id_function(route)


def run(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    uvicorn.run("engine.api.app:app", host=host, port=port, reload=reload)


app.mount("/css", StaticFiles(directory=STATIC_DIR / "css"), name="css")
app.mount("/icons", StaticFiles(directory=STATIC_DIR / "icons"), name="icons")
app.mount("/js", StaticFiles(directory=STATIC_DIR / "js"), name="js")
app.mount("/sg", SpaStaticFiles(directory=STATIC_DIR, html=True), name="sg")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="root")
