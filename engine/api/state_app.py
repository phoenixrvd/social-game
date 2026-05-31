from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field


RelativeUrl = Annotated[str, Field(pattern=r"^/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*$")]
EntityId = Annotated[str, Field(pattern=r"^[a-z0-9_]+$")]


def url_version(path: Path) -> str:
    if not path.exists():
        return ""
    stat = path.stat()
    return f"{stat.st_mtime_ns}-{stat.st_size}"
