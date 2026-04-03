from typing import Any


class FakeLogger:
    def __init__(self) -> None:
        self.messages: list[Any] = []

    def info(self, message: object, *args) -> None:
        if isinstance(message, str) and args:
            self.messages.append(message % args)
            return

        self.messages.append(message)

