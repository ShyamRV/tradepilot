"""Outbox worker entrypoint.

Docker / Render / Railway override:
  python -m apps.worker.main
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from tradepilot.controls import BetaControls
from tradepilot.durable import build_runtime
from tradepilot.logging_utils import configure_logging, init_sentry_stub
from tradepilot.messaging import TelegramAdapter, dispatch_outbox


def run_once(repository, sender, controls: BetaControls | None = None) -> int:
    """Dispatch one batch; deployment supplies a Telegram HTTP sender."""
    beta = controls or BetaControls()
    return dispatch_outbox(
        repository,
        TelegramAdapter(sender),
        lambda workspace_id: beta.flag(workspace_id, "notification_dispatch"),
    )


def _telegram_sender(token: str):
    def send(chat_id: str, text: str) -> None:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read()

    return send


def _poll_seconds() -> int:
    raw = os.getenv("WORKER_POLL_SECONDS") or os.getenv("TRADEPILOT_WORKER_INTERVAL_SECONDS") or "5"
    return max(1, int(raw))


def main() -> None:
    logger = configure_logging("worker")
    init_sentry_stub()
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    poll = _poll_seconds()
    repository, _auth = build_runtime()
    controls = BetaControls()

    if not token:
        logger.warning(
            "telegram_token_missing",
            extra={"event": "telegram_token_missing", "service": "worker"},
        )

        def sender(chat_id: str, text: str) -> None:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    else:
        sender = _telegram_sender(token)

    logger.info("worker_started", extra={"event": "worker_started", "service": "worker"})
    while True:
        try:
            sent = run_once(repository, sender, controls)
            if sent:
                logger.info(
                    "outbox_dispatched",
                    extra={"event": "outbox_dispatched", "service": "worker"},
                )
        except urllib.error.URLError:
            logger.error(
                "telegram_transport_error",
                extra={"event": "telegram_transport_error", "service": "worker"},
            )
        except Exception:
            logger.exception(
                "worker_iteration_failed",
                extra={"event": "worker_iteration_failed", "service": "worker"},
            )
        time.sleep(poll)


if __name__ == "__main__":
    main()
