from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import engine.llm_client as llm_client_module
from openai.types.chat import ChatCompletionMessageParam
from tests.fakes import FakeLogger


def test_stream_prompt_logs_usage_chunk_without_choices(monkeypatch):
    fake_logger = FakeLogger()

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

    monkeypatch.setattr(llm_client_module, "LOGGER", fake_logger)
    monkeypatch.setattr(llm_client_module, "OpenAI", lambda api_key: FakeClient())

    messages = [cast(ChatCompletionMessageParam, cast(object, {"role": "user", "content": "Hi"}))]
    parts = list(llm_client_module.stream_prompt(messages))

    assert parts == ["Hallo", " Welt"]
    assert fake_logger.messages == [{"event": "chat_tokens", "prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18, "cached_tokens": 3, "unavailable": False, "message_count": 1}]



