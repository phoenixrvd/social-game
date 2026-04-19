from io import BytesIO
from typing import Iterator, cast

from openai.types.chat import ChatCompletionMessageParam
from PIL import Image

from engine.config import Provider, config
from engine.llm.grok_provider_client import GrokProviderClient
from engine.llm.openai_provider_client import OpenAiProviderClient
from engine.llm.provider_client import ProviderClient


class CompressedImage:
    def __init__(self, name: str, image_bytes: bytes) -> None:
        self.name = name
        self.image_bytes = image_bytes

    def get(self, scale_factor: float = 0.9, quality: int = 88) -> tuple[str, bytes]:
        with Image.open(BytesIO(self.image_bytes)) as image:
            normalized = image.convert("RGBA")
            w = max(1, round(normalized.width * scale_factor))
            h = max(1, round(normalized.height * scale_factor))
            if normalized.size != (w, h):
                normalized = normalized.resize((w, h), Image.Resampling.LANCZOS)
            flattened = Image.new("RGB", normalized.size, (255, 255, 255))
            flattened.paste(normalized, mask=normalized.getchannel("A"))
            compressed = BytesIO()
            compressed.name = self.name
            flattened.save(compressed, format="JPEG", quality=quality, optimize=True, progressive=True)
            return self.name, compressed.getvalue()


class Client:
    def __init__(self) -> None:
        self._openai_provider = OpenAiProviderClient()
        self._grok_provider = GrokProviderClient()
        self._big_client = self._get_provider(config.LLM_BIG)
        self._small_client = self._get_provider(config.LLM_SMALL)
        self._image_client = self._get_provider(config.IMAGE)
        self._embedding_client = self._get_provider(config.EMBEDDING)

    def _get_provider(self, provider: Provider) -> ProviderClient:
        if provider == "grok":
            return self._grok_provider
        return self._openai_provider

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        cleaned = [t for t in texts if t.strip()]
        if not cleaned:
            return []
        return self._embedding_client.request_embeddings(cleaned)

    def stream_prompt(self, messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
        yield from self._big_client.request_big(messages)

    def run_prompt_small(self, prompt: str) -> str:
        cleaned = prompt.strip()
        if not cleaned:
            return ""
        user_message = cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": cleaned}))
        return self._small_client.request_small([user_message])

    def refresh_img(self, prompt: str, reference_img_bytes: bytes, identity_img_bytes: bytes | None = None) -> bytes:
        current = CompressedImage("current.jpg", reference_img_bytes).get(scale_factor=0.8, quality=82)
        if identity_img_bytes is None:
            images = [current]
        else:
            identity = CompressedImage("identity.jpg", identity_img_bytes).get(scale_factor=1.0, quality=92)
            images = [identity, current]
        return self._image_client.request_image(prompt, images)

    def merge_character_scene_img(self, prompt: str, character_img_bytes: bytes, scene_img_bytes: bytes) -> bytes:
        images = [
            CompressedImage("character.jpg", character_img_bytes).get(),
            CompressedImage("scene.jpg", scene_img_bytes).get(),
        ]
        return self._image_client.request_image(prompt, images)



client = Client()
