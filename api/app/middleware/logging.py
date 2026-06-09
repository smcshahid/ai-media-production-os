"""Structured access logging (T-03-02).

Pure-ASGI middleware that emits one JSON log line per HTTP request with method,
path, status code and wall-clock duration. The ``request_id`` is injected by the
logging filter (aimpos-config) from the context variable set by
``RequestIDMiddleware``, so access logs correlate with any logs the handler
emits. Status code is captured from the response-start message; timing wraps the
whole downstream call so it is logged even when the handler raises.
"""

from __future__ import annotations

import logging
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("aimpos.access")


class AccessLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500

        async def send_capturing_status(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_capturing_status)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            client = scope.get("client")
            logger.info(
                "http_request",
                extra={
                    "http_method": scope.get("method"),
                    "path": scope.get("path"),
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client": client[0] if client else None,
                },
            )
