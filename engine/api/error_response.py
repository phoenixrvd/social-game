from __future__ import annotations

from typing import Any

from engine.api.models import ApiModel


class ErrorResponse(ApiModel):
    type: str
    status: int
    detail: str | list[dict[str, Any]]


ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}
