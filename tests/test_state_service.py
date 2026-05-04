from __future__ import annotations

from types import SimpleNamespace

import engine.services.state_service as state_service_module
from engine.services.state_service import StateService


class FakeText:
    def __init__(self, value: str):
        self._value = value

    def get(self) -> str:
        return self._value


def test_normalize_state_output_removes_wrapping_markdown_fence() -> None:
    raw = """```markdown
trust: 68
comfort: 65

Freitext
```"""

    normalized = StateService._normalize_state_output(raw)

    assert normalized == "trust: 68\ncomfort: 65\n\nFreitext"


def test_run_update_saves_normalized_state(monkeypatch) -> None:
    saved: dict[str, str] = {}

    fake_storage = SimpleNamespace(
        prompts=SimpleNamespace(state_update=FakeText("{{CURRENT_STATE}}\n{{SHORT_TERM_MEMORY}}\n{{CURRENT_ETM}}")),
        npc=SimpleNamespace(
            state="trust: 50",
            stm=SimpleNamespace(text="user: hi"),
            state_runtime=SimpleNamespace(save=lambda value: saved.update({"value": value})),
        ),
    )
    monkeypatch.setattr(state_service_module, "storage", fake_storage)
    monkeypatch.setattr(state_service_module, "client", SimpleNamespace(run_prompt_small=lambda _prompt: "```\ntrust: 70\n\nOk\n```"))

    class FakeEtmService:
        def load_relevant(self, _text: str) -> str:
            return "- m"

    monkeypatch.setattr(state_service_module, "EtmService", FakeEtmService)

    service = StateService()
    result = service.run_update()

    assert result == "trust: 70\n\nOk"
    assert saved["value"] == "trust: 70\n\nOk"

