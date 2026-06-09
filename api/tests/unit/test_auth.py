"""Bearer auth middleware tests (US-25 / T-25-01).

Auth runs as middleware (before routing), so the 401 cases short-circuit before
any route dependency; the happy path is checked against a real protected route
(``GET /projects``) with the in-memory session override. ``/health`` must stay
reachable without a token.
"""

from __future__ import annotations

import httpx
import pytest
from aimpos_config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_health_checks, get_session
from app.infrastructure.health.probes import DependencyStatus
from app.main import create_app


def _transport(session: AsyncSession) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return httpx.ASGITransport(app=app)


def _valid_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_settings().api_token}"}


@pytest.mark.asyncio
async def test_missing_token_returns_401(session: AsyncSession) -> None:
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/projects")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_wrong_token_returns_401(session: AsyncSession) -> None:
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/projects", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_non_bearer_scheme_returns_401(session: AsyncSession) -> None:
    transport = _transport(session)
    header = {"Authorization": f"Basic {get_settings().api_token}"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/projects", headers=header)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_query_param_token_is_not_accepted(session: AsyncSession) -> None:
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/projects?token={get_settings().api_token}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_is_accepted(session: AsyncSession) -> None:
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/projects", headers=_valid_header())

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_is_exempt_from_auth() -> None:
    app = create_app()
    app.dependency_overrides[get_health_checks] = lambda: {
        name: DependencyStatus(status="ok") for name in ("postgresql", "redis", "minio")
    }
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
