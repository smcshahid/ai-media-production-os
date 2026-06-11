"""Bearer token authentication (US-25 / T-25-01).

Pure-ASGI middleware (same style as request-id / access-log, D-23). Every HTTP
request except ``GET /health`` must carry ``Authorization: Bearer <token>`` whose
value matches ``AIMPOS_API_TOKEN`` (via ``aimpos-config`` ``Settings``); otherwise
the request is rejected with **401** and a consistent ``{"detail": "Unauthorized"}``
body (Sprint 0 plan §4.5 DoD). The token is read from the ``Authorization`` header
only — there is no query-parameter fallback. ``/health`` is exempt so Docker
health checks and monitoring keep working.

For Sprint 0 this is a single shared static token (Keycloak is deferred to
Phase 1 — see DECISIONS D-09). Comparison uses ``secrets.compare_digest`` to avoid
leaking the token via timing.
"""

from __future__ import annotations

import secrets

from aimpos_config import get_settings
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

# Only operational/diagnostic endpoints are exempt (DoD §4.5: "all routes except
# /health return 401"). The OpenAPI/docs surface is therefore also protected.
_EXEMPT_PATHS = frozenset({"/health"})


class AuthMiddleware:
    """Reject unauthenticated HTTP requests to non-exempt paths with 401."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self._app(scope, receive, send)
            return

        if scope["type"] == "websocket" or scope["path"] in _EXEMPT_PATHS:
            await self._app(scope, receive, send)
            return

        if not _is_authorized(Headers(scope=scope).get("authorization")):
            response = JSONResponse(
                {"detail": "Unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)


def _is_authorized(header: str | None) -> bool:
    if header is None:
        return False
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return False
    expected = get_settings().api_token
    return bool(expected) and secrets.compare_digest(token, expected)
