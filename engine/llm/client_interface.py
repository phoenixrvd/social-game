from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from openai.types.chat import ChatCompletionMessageParam

NamedImage = tuple[str, bytes]


class ClientInterface(ABC):
    @abstractmethod
    def big_request(
        self,
        messages: list[ChatCompletionMessageParam],
        *,
        stream: bool,
    ) -> str | Iterator[str]:
        raise NotImplementedError

    @abstractmethod
    def small_request(
        self,
        messages: list[ChatCompletionMessageParam],
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def image_request(
        self,
        prompt: str,
        images: list[NamedImage],
    ) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def embedding_request(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        raise NotImplementedError


