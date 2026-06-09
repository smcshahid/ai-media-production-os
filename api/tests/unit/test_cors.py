"""CORS middleware tests (US-26 / TD-26).

The SPA runs on a different origin (``localhost:5173``) than the API, so the
browser issues a credential-less preflight ``OPTIONS`` before any real request.
CORS must sit outside Auth so that preflight is answered with 200 (not 401) and
real responses carry ``Access-Control-Allow-Origin``.
"""

from __future__ import annotations

import httpx
import pytest

from app.main import create_app

_ORIGIN = "http://localhost:5173"


@pytest.mark.asyncio
async def test_preflight_options_is_allowed_without_token() -> None:
    transport = httpx.ASGITransport(app=create_app())
    headers = {
        "Origin": _ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options("/assets", headers=headers)

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == _ORIGIN


@pytest.mark.asyncio
async def test_simple_request_echoes_allow_origin() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Unauthorized, but CORS headers must still be present on the response.
        response = await client.get("/projects", headers={"Origin": _ORIGIN})

    assert response.headers.get("access-control-allow-origin") == _ORIGIN


@pytest.mark.asyncio
async def test_unknown_origin_is_not_allowed() -> None:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/projects", headers={"Origin": "http://evil.example"})

    assert response.headers.get("access-control-allow-origin") is None
