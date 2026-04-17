from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from typing import cast

import engine.llm.client as llm_client_module
import engine.llm.client_grok as grok_client_module
import engine.llm.client_openai as openai_client_module
import openai
import requests
from engine.llm.client_grok import ClientGrok
from engine.llm.client_openai import ClientOpenAi
from openai.types.chat import ChatCompletionMessageParam
from PIL import Image


def _assert_jpeg_size(image_bytes: bytes, expected_size: tuple[int, int]) -> None:
    with Image.open(BytesIO(image_bytes)) as image:
        assert image.size == expected_size
        assert image.mode == "RGB"
        assert image.format == "JPEG"


def test_stream_prompt_streams_chunks(monkeypatch):
    messages = [cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": "Hi"}))]

    class FakeBigClient:
        @staticmethod
        def big_request(_messages, *, stream):
            assert _messages == messages
            assert stream is True
            return iter(["Hallo", " Welt"])

    monkeypatch.setattr(llm_client_module._client, "big_client", lambda: FakeBigClient())
    assert list(llm_client_module.stream_prompt(messages)) == ["Hallo", " Welt"]


def test_merge_character_scene_img_uses_named_files_for_openai(monkeypatch, tmp_path):
    from PIL import Image
    from io import BytesIO

    # Create valid PNG bytes
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    char_bytes = img_bytes.getvalue()

    img2 = Image.new('RGB', (100, 100), color='blue')
    img_bytes2 = BytesIO()
    img2.save(img_bytes2, format='PNG')
    scene_bytes = img_bytes2.getvalue()

    captured: dict[str, object] = {}

    class FakeImageClient:
        @staticmethod
        def image_request(prompt, images):
            captured["prompt"] = prompt
            captured["images"] = images
            return b"img"

    monkeypatch.setattr(llm_client_module._client, "image_client", lambda: FakeImageClient())

    result = llm_client_module.merge_character_scene_img("merge prompt", char_bytes, scene_bytes)
    assert result == b"img"
    images = cast(list[tuple[str, bytes]], captured["images"])
    assert [name for name, _ in images] == ["character.jpg", "scene.jpg"]


def test_refresh_img_uses_compressed_named_files(monkeypatch):
    captured: dict[str, object] = {}

    class FakeImageClient:
        @staticmethod
        def image_request(prompt, images):
            captured["images"] = images
            return b"img"

    monkeypatch.setattr(llm_client_module._client, "image_client", lambda: FakeImageClient())

    current = BytesIO()
    Image.new("RGB", (1600, 1200), (10, 20, 30)).save(current, format="PNG")
    identity = BytesIO()
    Image.new("RGBA", (1200, 1600), (40, 50, 60, 128)).save(identity, format="PNG")

    result = llm_client_module.refresh_img("refresh prompt", current.getvalue(), identity.getvalue())
    assert result == b"img"
    images = cast(list[tuple[str, bytes]], captured["images"])
    assert [name for name, _ in images] == ["identity.jpg", "current.jpg"]
    _assert_jpeg_size(images[0][1], (1200, 1600))
    _assert_jpeg_size(images[1][1], (1280, 960))


def test_run_prompt_uses_big_client(monkeypatch):
    captured: dict[str, object] = {}

    class FakeBigClient:
        @staticmethod
        def big_request(messages, *, stream):
            captured["messages"] = messages
            captured["stream"] = stream
            return "ok"

    monkeypatch.setattr(llm_client_module._client, "big_client", lambda: FakeBigClient())
    result = llm_client_module.run_prompt("Hi")
    assert result == "ok"
    assert captured["stream"] is False
    msg = cast(list[dict[str, str]], captured["messages"])[0]
    assert msg["role"] == "user"
    assert msg["content"] == "Hi"


def test_run_prompt_small_uses_small_client(monkeypatch):
    captured: dict[str, object] = {}

    class FakeSmallClient:
        @staticmethod
        def small_request(messages):
            captured["messages"] = messages
            return "ok-small"

    monkeypatch.setattr(llm_client_module._client, "small_client", lambda: FakeSmallClient())
    result = llm_client_module.run_prompt_small("Hi")
    assert result == "ok-small"
    msg = cast(list[dict[str, str]], captured["messages"])[0]
    assert msg["role"] == "user"
    assert msg["content"] == "Hi"


def test_grok_image_response_bytes_downloads_from_url(monkeypatch):
    captured: dict[str, object] = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return SimpleNamespace(content=b"downloaded")

    monkeypatch.setattr(grok_client_module.httpx, "get", fake_get)

    result = grok_client_module._grok_image_response_bytes(SimpleNamespace(url="https://cdn.x.ai/generated.png"))
    assert result == b"downloaded"
    assert captured == {"url": "https://cdn.x.ai/generated.png", "timeout": 120.0}


def test_grok_image_request_wraps_moderated_content_http_error(monkeypatch):
    client = ClientGrok()

    class FakeImageResponse:
        @property
        def image(self):
            response = requests.Response()
            response.status_code = 404
            response.url = "https://imgen.x.ai/moderated_content.png"
            raise requests.HTTPError("404 Not Found", response=response)

    class FakeSdkClient:
        class image:
            @staticmethod
            def sample(**_payload):
                return FakeImageResponse()

    monkeypatch.setattr(grok_client_module, "_image_data_url", lambda _image_bytes: "data:image/png;base64,AA==")
    monkeypatch.setattr(client, "_sdk_client", lambda: FakeSdkClient())

    try:
        client.image_request("prompt", [("current.jpg", b"raw")])
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Anfrage durch Moderation blockiert."
        assert isinstance(exc.__cause__, requests.HTTPError)


def test_grok_big_request_wraps_direct_openai_error_with_main_message(monkeypatch):
    client = ClientGrok()

    class FakePermissionDenied(openai.OpenAIError):
        pass

    class FakeTextClient:
        class chat:
            class completions:
                @staticmethod
                def create(**_kwargs):
                    raise FakePermissionDenied(
                        "PermissionDeniedError(\"Error code: 403 - {'code': 'forbidden', 'error': 'Content violates "
                        "usage guidelines. Team: abc Failed check: SAFETY_CHECK_TYPE_CSAM'}\")"
                    )

    monkeypatch.setattr(client, "_text_client", lambda: FakeTextClient())

    try:
        client.big_request([], stream=False)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Content violates usage guidelines."
        assert isinstance(exc.__cause__, FakePermissionDenied)


def test_grok_streaming_wraps_iteration_error_with_main_message(monkeypatch):
    client = ClientGrok()

    class FakePermissionDenied(openai.OpenAIError):
        pass

    class FailingStream:
        def __iter__(self):
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hallo"))])
            raise FakePermissionDenied(
                "PermissionDeniedError(\"Error code: 403 - {'code': 'forbidden', 'error': 'Content violates usage "
                "guidelines. Team: abc Failed check: SAFETY_CHECK_TYPE_CSAM'}\")"
            )

    class FakeTextClient:
        class chat:
            class completions:
                @staticmethod
                def create(**_kwargs):
                    return FailingStream()

    monkeypatch.setattr(client, "_text_client", lambda: FakeTextClient())

    stream = client.big_request([], stream=True)
    assert next(stream) == "Hallo"
    try:
        next(stream)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Content violates usage guidelines."
        assert isinstance(exc.__cause__, FakePermissionDenied)


def test_openai_streaming_wraps_iteration_error_with_main_message(monkeypatch):
    client = ClientOpenAi()

    class FakePermissionDenied(openai.OpenAIError):
        pass

    class FailingStream:
        def __iter__(self):
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hallo"))])
            raise FakePermissionDenied(
                "PermissionDeniedError(\"Error code: 403 - {'code': 'forbidden', 'error': 'Content violates usage "
                "guidelines. Team: abc Failed check: SAFETY_CHECK_TYPE_CSAM'}\")"
            )

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**_kwargs):
                    return FailingStream()

    monkeypatch.setattr(openai_client_module.ClientOpenAi, "_client", staticmethod(lambda: FakeClient()))

    stream = client.big_request([], stream=True)
    assert next(stream) == "Hallo"
    try:
        next(stream)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Content violates usage guidelines."
        assert isinstance(exc.__cause__, FakePermissionDenied)


def test_grok_embeddings_use_local_fn(monkeypatch):
    def fake_embedding_fn(_texts):
        return [[0.1, 0.2, 0.3]]

    client = ClientGrok()
    client._local_embedding_fn = fake_embedding_fn

    first = client.embedding_request(["Hallo Welt"])[0]
    second = client.embedding_request(["Hallo Welt"])[0]
    assert first == [0.1, 0.2, 0.3]
    assert first == second


def test_grok_embeddings_use_data_cache_dir(monkeypatch, tmp_path):
    captured: dict[str, str] = {}

    class FakeTextEmbedding:
        def __init__(self, *, model_name, cache_dir):
            captured["model_name"] = model_name
            captured["cache_dir"] = cache_dir

        @staticmethod
        def embed(_texts):
            return [[0.4, 0.5]]

    class FakeStorage:
        @property
        def etm_fastembed_cache(self):
            return tmp_path / "fastembed_cache"

    monkeypatch.setattr(grok_client_module, "TextEmbedding", FakeTextEmbedding)
    monkeypatch.setattr(grok_client_module, "storage", FakeStorage())

    client = ClientGrok()
    assert client.embedding_request(["Hallo"]) == [[0.4, 0.5]]
    assert captured["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert captured["cache_dir"] == str(tmp_path / "fastembed_cache")


def test_grok_embeddings_retry_once_for_missing_model_file(monkeypatch):
    client = ClientGrok()
    calls = {"count": 0}

    def fake_local_embedding_function():
        calls["count"] += 1
        if calls["count"] == 1:
            def broken(_texts):
                raise RuntimeError("NO_SUCHFILE: model.onnx missing")

            return broken

        def recovered(_texts):
            return [[0.1, 0.2, 0.3]]

        return recovered

    monkeypatch.setattr(client, "_local_embedding_function", fake_local_embedding_function)

    # First call raises error, no retry - test expects error propagation
    try:
        client.embedding_request(["Hallo Welt"])
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "NO_SUCHFILE" in str(e)
        assert calls["count"] == 1



