from __future__ import annotations

from pydantic import BaseModel, ConfigDict

SHORT_TEXT_MAX_LENGTH = 256
CHAT_MESSAGE_MAX_LENGTH = 4_000
LONG_TEXT_MAX_LENGTH = 12_000
USER_PROFILE_MAX_LENGTH = 8_000
DATA_URL_MAX_LENGTH = 5 * 1024 * 1024


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
