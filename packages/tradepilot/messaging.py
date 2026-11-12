from __future__ import annotations

from typing import Callable, Protocol

from .core import Repository


class TelegramTransport(Protocol):
    def send(self, chat_id: str, text: str) -> None: ...


class TelegramAdapter:
    def __init__(self, sender: Callable[[str, str], None]) -> None:
        self._sender = sender

    def send(self, chat_id: str, text: str) -> None:
        if not chat_id or not text or len(text) > 4096:
            raise ValueError("invalid Telegram message")
        self._sender(chat_id, text)


def dispatch_outbox(
    repo: Repository,
    transport: TelegramTransport,
    feature_enabled: Callable[[str], bool] = lambda _: True,
) -> int:
    sent = 0
    for message in repo.pending():
        if not feature_enabled(message.tenant_id):
            continue
        transport.send(str(message.payload["chat_id"]), str(message.payload["text"]))
        repo.mark_sent(message.id)
        sent += 1
    return sent
