"""Structured JSON logging helpers and optional Sentry DSN stub."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", os.getenv("TRADEPILOT_SERVICE", "api")),
            "event": getattr(record, "event", record.getMessage()),
            "logger": record.name,
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(service: str = "api") -> logging.Logger:
    os.environ.setdefault("TRADEPILOT_SERVICE", service)
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
    logger = logging.getLogger("tradepilot")
    logger.info("logging_configured", extra={"event": "logging_configured", "service": service})
    return logger


def init_sentry_stub() -> bool:
    """Reserve SENTRY_DSN wiring without requiring sentry-sdk at install time.

    Returns True when a DSN is present (operators should install sentry-sdk and
    replace this stub before production). Returns False when unset.
    """
    dsn = (os.getenv("SENTRY_DSN") or "").strip()
    logger = logging.getLogger("tradepilot")
    if not dsn:
        logger.info("sentry_disabled", extra={"event": "sentry_disabled", "service": os.getenv("TRADEPILOT_SERVICE", "api")})
        return False
    # Stub only: do not import sentry-sdk here so the base image stays lean until
    # the secrets manager provisions a real DSN and the dependency is added.
    logger.warning(
        "sentry_dsn_present_sdk_not_initialized",
        extra={"event": "sentry_dsn_present_sdk_not_initialized", "service": os.getenv("TRADEPILOT_SERVICE", "api")},
    )
    return True


def readiness_status() -> tuple[dict[str, Any], int]:
    """Return readiness payload and HTTP status for /ready probes."""
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    db_path = (os.getenv("TRADEPILOT_DB_PATH") or "").strip()
    checks: dict[str, str] = {"app": "ok"}
    ready = True

    if database_url:
        # Persistence adapter is still in-memory by default; report configured
        # vs connected so operators can distinguish packaging from cutover.
        checks["database_url"] = "configured"
        try:
            import urllib.parse

            parsed = urllib.parse.urlparse(database_url)
            if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
                checks["database_url"] = "invalid"
                ready = False
        except Exception:
            checks["database_url"] = "invalid"
            ready = False
    else:
        checks["database_url"] = "unconfigured"

    if db_path:
        checks["db_path"] = "configured" if os.path.exists(os.path.dirname(db_path) or ".") else "missing_parent"
        if checks["db_path"] != "configured":
            ready = False
    else:
        checks["db_path"] = "unconfigured"

    # In-memory MVP remains ready for traffic even without Postgres; durable
    # cutover should tighten this check once the repository adapter connects.
    status = "ready" if ready else "not_ready"
    return {"status": status, "checks": checks}, (200 if ready else 503)
