from io import BytesIO
from typing import Iterator

from openai.types.chat import ChatCompletionMessageParam
from PIL import Image

from engine.config import config
from engine.llm.client_adapter import ClientAdapter
from engine.llm.client_interface import ClientInterface

_client = ClientAdapter()


def _user_message(content: str) -> ChatCompletionMessageParam:
    from typing import cast
    return cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": content}))


def _active_small_model_name() -> str:
    if config.LLM_SMALL == "grok":
        return config.GROK_MODEL_LLM_SMALL
    return config.OPENAI_MODEL_LLM_SMALL


def _active_big_model_name() -> str:
    if config.LLM_BIG == "grok":
        return config.GROK_MODEL_LLM_BIG
    return config.OPENAI_MODEL_LLM_BIG


def _small_llm_client() -> ClientInterface:
    return _client.small_client()


def _big_llm_client() -> ClientInterface:
    return _client.big_client()


def _image_client() -> ClientInterface:
    return _client.image_client()


def _embedding_client() -> ClientInterface:
    return _client.embedding_client()


def _compress_image(image_bytes: bytes, *, filename: str, scale_factor: float, quality: int) -> BytesIO:
    with Image.open(BytesIO(image_bytes)) as image:
        normalized = image.convert("RGBA")
        w = max(1, round(normalized.width * scale_factor))
        h = max(1, round(normalized.height * scale_factor))
        if normalized.size != (w, h):
            normalized = normalized.resize((w, h), Image.Resampling.LANCZOS)
        flattened = Image.new("RGB", normalized.size, (255, 255, 255))
        flattened.paste(normalized, mask=normalized.getchannel("A"))
        compressed = BytesIO()
        compressed.name = filename
        flattened.save(compressed, format="JPEG", quality=quality, optimize=True, progressive=True)
        compressed.seek(0)
        return compressed


def hello_llm() -> str:
    small_model = _active_small_model_name()
    big_model = _active_big_model_name()
    small = _small_llm_client().small_request(
        [_user_message(f"Antworte nur mit: Hallo aus dem SML ({small_model})")],
    )
    big = _big_llm_client().big_request(
        [_user_message(f"Antworte nur mit: Hallo aus dem LLM ({big_model})")],
        stream=False,
    )
    return "\n".join([small, str(big)])


def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned = [t for t in texts if t.strip()]
    if not cleaned:
        return []
    return _embedding_client().embedding_request(cleaned)



def stream_prompt(messages: list[ChatCompletionMessageParam]) -> Iterator[str]:
    stream = _big_llm_client().big_request(messages, stream=True)
    if isinstance(stream, str):
        yield stream
        return
    yield from stream


def run_prompt(prompt: str) -> str:
    cleaned = prompt.strip()
    if not cleaned:
        return ""
    return str(_big_llm_client().big_request([_user_message(cleaned)], stream=False))


def run_prompt_small(prompt: str) -> str:
    cleaned = prompt.strip()
    if not cleaned:
        return ""
    return _small_llm_client().small_request([_user_message(cleaned)])


def refresh_img(prompt: str, reference_img_bytes: bytes, identity_img_bytes: bytes | None = None) -> bytes:
    current = _compress_image(reference_img_bytes, filename="current.jpg", scale_factor=0.8, quality=82)
    if identity_img_bytes is None:
        images = [("current.jpg", current.getvalue())]
    else:
        identity = _compress_image(identity_img_bytes, filename="identity.jpg", scale_factor=1.0, quality=92)
        images = [("identity.jpg", identity.getvalue()), ("current.jpg", current.getvalue())]
    return _image_client().image_request(prompt, images)


def merge_character_scene_img(prompt: str, character_img_bytes: bytes, scene_img_bytes: bytes) -> bytes:
    images = [
        ("character.jpg", _compress_image(character_img_bytes, filename="character.jpg", scale_factor=0.9, quality=88).getvalue()),
        ("scene.jpg", _compress_image(scene_img_bytes, filename="scene.jpg", scale_factor=0.9, quality=88).getvalue()),
    ]
    return _image_client().image_request(prompt, images)

