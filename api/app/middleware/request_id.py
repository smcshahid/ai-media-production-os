"""Request-ID propagation (T-03-03).

Pure-ASGI middleware (not ``BaseHTTPMiddleware``) so the context variable is set
in the same context the endpoint runs in — guaranteeing every log line emitted
while handling the request carries the same ``request_id``. The id is taken from
an inbound ``X-Request-ID`` header when present (so a caller/proxy can correlate
across services), otherwise a UUID4 is generated. It is always echoed back on
the response.
"""

from __future__ import annotations

from uuid import uuid4

from aimpos_config.logging import request_id_var
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp, header_name: str = REQUEST_ID_HEADER) -> None:
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        inbound = Headers(scope=scope).get(self.header_name)
        request_id = inbound or str(uuid4())
        token = request_id_var.set(request_id)

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers[self.header_name] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            request_id_var.reset(token)
