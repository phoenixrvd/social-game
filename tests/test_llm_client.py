from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from typing import Iterator, cast

import engine.client as llm_client_module
import openai
from openai.types.chat import ChatCompletionMessageParam
from PIL import Image


def _assert_jpeg_size(image_bytes: bytes, expected_size: tuple[int, int]) -> None:
    with Image.open(BytesIO(image_bytes)) as image:
        assert image.size == expected_size
        assert image.mode == "RGB"
        assert image.format == "JPEG"


def _require_iterator(stream: str | Iterator[str]) -> Iterator[str]:
    if isinstance(stream, str):
        raise AssertionError("Expected streaming iterator")
    return stream


def _next_chunk(stream: Iterator[str]) -> str:
    return next(stream)


def test_stream_prompt_streams_chunks(monkeypatch):
    messages = [cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": "Hi"}))]

    class FakeBigClient:
        @staticmethod
        def _request_big(_messages):
            assert _messages == messages
            return iter(["Hallo", " Welt"])

    monkeypatch.setattr(llm_client_module.client, "_request_big", FakeBigClient()._request_big)
    assert list(llm_client_module.client.stream_prompt(messages)) == ["Hallo", " Welt"]


def test_stream_prompt_delegates_to_big_request_without_tools_override(monkeypatch):
    messages = [cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": "Hi"}))]
    captured: dict[str, object] = {}

    class FakeBigClient:
        @staticmethod
        def _request_big(_messages):
            captured["messages"] = _messages
            return iter(["ok"])

    monkeypatch.setattr(llm_client_module.client, "_request_big", FakeBigClient()._request_big)

    assert list(llm_client_module.client.stream_prompt(messages)) == ["ok"]
    assert captured["messages"] == messages


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
        def _request_image(prompt, images):
            captured["prompt"] = prompt
            captured["images"] = images
            return b"img"

    monkeypatch.setattr(llm_client_module.client, "_request_image", FakeImageClient()._request_image)

    result = llm_client_module.client.merge_character_scene_img("merge prompt", char_bytes, scene_bytes)
    assert result == b"img"
    images = cast(list[tuple[str, bytes]], captured["images"])
    assert [name for name, _ in images] == ["character.jpg", "scene.jpg"]


def test_refresh_img_uses_compressed_named_files(monkeypatch):
    captured: dict[str, object] = {}

    class FakeImageClient:
        @staticmethod
        def _request_image(prompt, images):
            captured["images"] = images
            return b"img"

    monkeypatch.setattr(llm_client_module.client, "_request_image", FakeImageClient()._request_image)

    current = BytesIO()
    Image.new("RGB", (1600, 1200), (10, 20, 30)).save(current, format="PNG")
    identity = BytesIO()
    Image.new("RGBA", (1200, 1600), (40, 50, 60, 128)).save(identity, format="PNG")

    result = llm_client_module.client.refresh_img("refresh prompt", current.getvalue(), identity.getvalue())
    assert result == b"img"
    images = cast(list[tuple[str, bytes]], captured["images"])
    assert [name for name, _ in images] == ["identity.jpg", "current.jpg"]
    _assert_jpeg_size(images[0][1], (1200, 1600))
    _assert_jpeg_size(images[1][1], (1280, 960))



def test_run_prompt_small_uses_small_client(monkeypatch):
    captured: dict[str, object] = {}

    class FakeSmallClient:
        @staticmethod
        def _request_small(messages):
            captured["messages"] = messages
            return "ok-small"

    monkeypatch.setattr(llm_client_module.client, "_request_small", FakeSmallClient()._request_small)
    result = llm_client_module.client.run_prompt_small("Hi")
    assert result == "ok-small"
    msg = cast(list[dict[str, str]], captured["messages"])[0]
    assert msg["role"] == "user"
    assert msg["content"] == "Hi"


def test_openai_streaming_wraps_iteration_error_with_main_message(monkeypatch):
    client = llm_client_module.Client()

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

    monkeypatch.setattr(llm_client_module.Client, "_text_client", staticmethod(lambda: FakeClient()))

    stream = _require_iterator(client._request_big([]))
    assert _next_chunk(stream) == "Hallo"
    try:
        _next_chunk(stream)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Content violates usage guidelines."
        assert isinstance(exc.__cause__, FakePermissionDenied)


def test_openai_big_request_sends_no_tools(monkeypatch):
    captured: dict[str, object] = {}

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured.update(kwargs)
                    return [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="ok"))])]

    client = llm_client_module.Client()
    monkeypatch.setattr(llm_client_module.Client, "_text_client", staticmethod(lambda: FakeClient()))

    assert list(client._request_big([])) == ["ok"]
    assert "tools" not in captured


def test_openai_small_request_sends_no_tools(monkeypatch):
    captured: dict[str, object] = {}

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured.update(kwargs)
                    return [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="ok"))])]

    client = llm_client_module.Client()
    monkeypatch.setattr(llm_client_module.Client, "_text_client", staticmethod(lambda: FakeClient()))

    assert client._request_small([]) == "ok"
    assert "tools" not in captured


def test_embed_texts_uses_configured_embedding_model(monkeypatch):
    captured: dict[str, object] = {}
    client = llm_client_module.Client()

    class FakeClient:
        class embeddings:
            @staticmethod
            def create(**kwargs):
                captured.update(kwargs)
                return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2])])

    monkeypatch.setattr(llm_client_module.config, "MODEL_EMBEDDING", "text-embedding-test")
    monkeypatch.setattr(llm_client_module.Client, "_text_client", staticmethod(lambda: FakeClient()))

    result = client.embed_texts(" Hallo ")

    assert result == [0.1, 0.2]
    assert captured["model"] == "text-embedding-test"
    assert captured["input"] == ["Hallo"]


def test_embed_texts_skips_blank_input_without_request(monkeypatch):
    client = llm_client_module.Client()
    monkeypatch.setattr(client, "_request_embedding", lambda _text: (_ for _ in ()).throw(AssertionError("should not run")))

    assert client.embed_texts("   ") == []



