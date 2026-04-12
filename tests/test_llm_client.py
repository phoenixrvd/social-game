from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from typing import cast

import engine.llm_client as llm_client_module
from openai.types.chat import ChatCompletionMessageParam
from PIL import Image


def test_stream_prompt_streams_chunks_with_usage_chunk_without_choices(monkeypatch):
    class FakeCompletions:
        @staticmethod
        def create(**_kwargs):
            return iter([
                SimpleNamespace(
                    usage=SimpleNamespace(
                        prompt_tokens=11,
                        completion_tokens=7,
                        total_tokens=18,
                        prompt_tokens_details=SimpleNamespace(cached_tokens=3),
                    ),
                    choices=[],
                ),
                SimpleNamespace(
                    usage=None,
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="Hallo"))],
                ),
                SimpleNamespace(
                    usage=None,
                    choices=[SimpleNamespace(delta=SimpleNamespace(content=" Welt"))],
                ),
            ])

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(llm_client_module, "OpenAI", lambda api_key: FakeClient())

    messages = [cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": "Hi"}))]
    parts = list(llm_client_module.stream_prompt(messages))

    assert parts == ["Hallo", " Welt"]


def test_merge_character_scene_img_uses_named_files(monkeypatch):
    captured: dict[str, object] = {}

    class FakeImages:
        @staticmethod
        def edit(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(b64_json="aW1n")])

    class FakeClient:
        images = FakeImages()

    monkeypatch.setattr(llm_client_module, "OpenAI", lambda api_key: FakeClient())

    result = llm_client_module.merge_character_scene_img(
        "merge prompt",
        b"character-bytes",
        b"scene-bytes",
    )

    assert result == b"img"
    image_files = captured["image"]
    assert isinstance(image_files, list)
    assert len(image_files) == 2
    assert image_files[0].name == "character.png"
    assert image_files[1].name == "scene.png"


def test_refresh_img_uses_compressed_named_files(monkeypatch):
    captured: dict[str, object] = {}

    class FakeImages:
        @staticmethod
        def edit(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(b64_json="aW1n")])

    class FakeClient:
        images = FakeImages()

    monkeypatch.setattr(llm_client_module, "OpenAI", lambda api_key: FakeClient())

    current = BytesIO()
    Image.new("RGB", (1600, 1200), (10, 20, 30)).save(current, format="PNG")
    identity = BytesIO()
    Image.new("RGBA", (1200, 1600), (40, 50, 60, 128)).save(identity, format="PNG")

    result = llm_client_module.refresh_img(
        "refresh prompt",
        current.getvalue(),
        identity.getvalue(),
    )

    assert result == b"img"
    image_files = captured["image"]
    assert isinstance(image_files, list)
    assert len(image_files) == 2
    assert image_files[0].name == "identity.jpg"
    assert image_files[1].name == "current.jpg"

    image_files[0].seek(0)
    image_files[1].seek(0)
    with Image.open(image_files[0]) as identity_image:
        assert identity_image.size == (1200, 1600)
        assert identity_image.mode == "RGB"
        assert identity_image.format == "JPEG"
    with Image.open(image_files[1]) as current_image:
        assert current_image.size == (1280, 960)
        assert current_image.mode == "RGB"
        assert current_image.format == "JPEG"


def test_scaled_dimensions_scales_from_original_size_and_honors_limits():
    assert llm_client_module._scaled_dimensions(
        1024,
        1536,
        scale_factor=0.8,
    ) == (819, 1229)
    assert llm_client_module._scaled_dimensions(
        400,
        600,
        scale_factor=0.8,
    ) == (320, 480)
