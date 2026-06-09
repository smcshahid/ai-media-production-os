"""Structured (JSON) logging for Sprint 0.

Logs are emitted as single-line JSON so they are greppable in `docker compose
logs`. A `request_id` is carried in a context variable (set by the API's
request-id middleware, T-03-03) and injected into every record by
``RequestIdFilter`` so all logs emitted while handling a request share the same
correlation id. Full OpenTelemetry instrumentation (Technology Recommendations
§4.8) lands with the observability stack in a later sprint.
"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from typing import Any

# Set per-request by the API middleware; ``None`` outside a request (e.g. at
# startup). Lives here so api and worker share one correlation mechanism.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_RESERVED = frozenset(logging.makeLogRecord({}).__dict__.keys()) | {
    "message",
    "asctime",
    "taskName",
}


class RequestIdFilter(logging.Filter):
    """Attach the current ``request_id`` (if any) to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        request_id = request_id_var.get()
        if request_id is not None:
            record.request_id = request_id
        return True


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
    """Install the JSON formatter + request-id filter on the root logger.

    Idempotent: replaces existing handlers so repeated calls (e.g. per test
    app) don't stack duplicate output.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
