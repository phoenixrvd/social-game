from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_EDGE = 1536

_webp_cache: dict[str, dict[str, Any]] = {}


def cached_webp_bytes(image_path: Path, max_width: int | None = None) -> bytes:
    stat = image_path.stat()
    signature = f"{stat.st_mtime_ns}|{stat.st_size}"
    width_key = "orig" if max_width is None else str(max_width)
    cache_key = f"{image_path}|{width_key}"

    cached = _webp_cache.get(cache_key)
    if cached and cached["signature"] == signature:
        return cached["data"]

    buffer = BytesIO()
    with Image.open(image_path) as image:
        if max_width is not None and image.width > max_width:
            ratio = max_width / image.width
            target_height = max(1, int(image.height * ratio))
            image = image.resize((max_width, target_height), Image.Resampling.LANCZOS)
        image.save(buffer, format="WEBP", quality=82, method=4)

    _webp_cache[cache_key] = {"signature": signature, "data": buffer.getvalue()}
    return _webp_cache[cache_key]["data"]


def decode_image_data_url(data_url: str) -> bytes:
    header, separator, payload = data_url.partition(",")
    if separator != "," or not header.startswith("data:image/") or ";base64" not in header:
        raise ValueError("Ungültiges Bildformat.")
    if not header.startswith(("data:image/png", "data:image/jpeg", "data:image/webp")):
        raise ValueError("Nur PNG, JPEG oder WebP sind erlaubt.")
    return base64.b64decode(payload, validate=True)


def encode_png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.convert("RGBA").save(buffer, format="PNG")
    return buffer.getvalue()


def normalize_image_data_url(data_url: str) -> bytes:
    image_bytes = decode_image_data_url(data_url)
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("Bild ist größer als 5 MB.")
    with Image.open(BytesIO(image_bytes)) as image:
        image.verify()
    with Image.open(BytesIO(image_bytes)) as image:
        if image.width > MAX_IMAGE_EDGE or image.height > MAX_IMAGE_EDGE:
            raise ValueError("Bildkante ist größer als 1536 px.")
        return encode_png(image)


def png_data_url(image_bytes: bytes) -> str:
    with Image.open(BytesIO(image_bytes)) as image:
        encoded = base64.b64encode(encode_png(image)).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def is_image_backup_name(value: str) -> bool:
    if len(value) != len("img-20260510-123456.png"):
        return False
    if not value.startswith("img-") or not value.endswith(".png"):
        return False

    timestamp = value.removeprefix("img-").removesuffix(".png")
    return len(timestamp) == 15 and timestamp[8] == "-" and timestamp.replace("-", "").isdigit()
