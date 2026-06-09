"""Minimal structured (JSON) logging for Sprint 0.

T-03-01 only needs logs to be emitted as single-line JSON so they are greppable
in `docker compose logs`. Request-id correlation and the access-log middleware
arrive with T-03-02 / T-03-03; full OpenTelemetry instrumentation lands with the
observability stack (Technology Recommendations §4.8) in a later sprint.
"""

from __future__ import annotations

import json
import logging
from typing import Any

_RESERVED = frozenset(logging.makeLogRecord({}).__dict__.keys()) | {
    "message",
    "asctime",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Render log records as a single line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
