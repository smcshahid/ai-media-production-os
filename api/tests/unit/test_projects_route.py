"""GET /projects route tests (T-01-03).

Uses httpx ASGITransport with an overridden session so the route shares the
in-memory test DB (and runs in the test's event loop); lifespan is not invoked,
so no real PostgreSQL/Redis is required.
"""

from __future__ import annotations

import httpx
import pytest
from aimpos_config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.domain.studio.project import DEFAULT_PROJECT_NAME
from app.main import create_app
from app.seed.default_project import seed_default_project

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


def _app_with_session(session: AsyncSession) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return httpx.ASGITransport(app=app)


@pytest.mark.asyncio
async def test_get_projects_returns_seeded_project(session: AsyncSession) -> None:
    await seed_default_project(session)
    transport = _app_with_session(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/projects", headers=_AUTH)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == DEFAULT_PROJECT_NAME
    assert body[0]["status"] == "ACTIVE"
    assert "id" in body[0]


@pytest.mark.asyncio
async def test_get_projects_empty_when_unseeded(session: AsyncSession) -> None:
    transport = _app_with_session(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/projects", headers=_AUTH)

    assert response.status_code == 200
    assert response.json() == []


def test_projects_is_registered_in_openapi() -> None:
    schema = create_app().openapi()
    assert "/projects" in schema["paths"]
    assert "get" in schema["paths"]["/projects"]
