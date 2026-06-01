from __future__ import annotations

from typing import Any

from pydantic import Field

from engine.api.models import ApiModel


class ErrorResponse(ApiModel):
    type: str = Field(description="Problem-Typ nach RFC 7807; derzeit 'about:blank' für generische Fehler.")
    status: int = Field(description="HTTP-Statuscode der fehlgeschlagenen Anfrage.")
    detail: str | list[dict[str, Any]] = Field(
        description="Nutzerlesbare Fehlermeldung oder strukturierte Validierungsdetails."
    )


ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}
