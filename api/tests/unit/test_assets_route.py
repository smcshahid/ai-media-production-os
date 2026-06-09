"""POST /assets + GET /assets route tests.

httpx ASGITransport with overridden ``get_session`` (in-memory SQLite) and
``get_minio`` (fake blob store) so no real PostgreSQL/MinIO is required and
lifespan is not invoked.
"""

from __future__ import annotations

import hashlib
import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository
from app.main import create_app

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


class _FakeBlobStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        self.objects[key] = data
        return hashlib.md5(data).hexdigest()  # mimics MinIO single-PUT ETag

    async def download_bytes(self, key: str) -> bytes:
        return self.objects[key]


def _transport(session: AsyncSession, blobs: _FakeBlobStore) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_minio] = lambda: blobs
    return httpx.ASGITransport(app=app)


async def _seed_project(session: AsyncSession) -> Project:
    project = Project(name="Asset Route Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()
    return project


@pytest.mark.asyncio
async def test_post_assets_creates_version(session: AsyncSession) -> None:
    project = await _seed_project(session)
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/assets",
            data={"project_id": str(project.id), "stage": "IDEA"},
            files={"file": ("idea.txt", b"hello idea", "text/plain")},
            headers=_AUTH,
        )

    assert response.status_code == 201
    body = response.json()
    assert body["version"] == 1
    assert body["stage"] == "IDEA"
    assert body["is_ai_generated"] is False
    assert len(body["content_hash"]) == 64
    assert body["minio_key"].endswith(body["content_hash"])
    assert "created_at" in body
    assert len(blobs.objects) == 1


@pytest.mark.asyncio
async def test_post_assets_unknown_project_returns_404(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/assets",
            data={"project_id": str(uuid.uuid4()), "stage": "IDEA"},
            files={"file": ("x.txt", b"x", "text/plain")},
            headers=_AUTH,
        )

    assert response.status_code == 404
    assert blobs.objects == {}  # nothing uploaded for a missing project


@pytest.mark.asyncio
async def test_get_assets_lists_versions_and_dedups(session: AsyncSession) -> None:
    project = await _seed_project(session)
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(2):
            await client.post(
                "/assets",
                data={"project_id": str(project.id), "stage": "IDEA"},
                files={"file": ("a.txt", b"same bytes", "text/plain")},
                headers=_AUTH,
            )
        response = await client.get(
            "/assets", params={"project_id": str(project.id)}, headers=_AUTH
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {row["version"] for row in body} == {1, 2}
    assert body[0]["minio_key"] == body[1]["minio_key"]  # dedup: one blob key
    assert len(blobs.objects) == 1


@pytest.mark.asyncio
async def test_get_assets_empty_for_unknown_project(session: AsyncSession) -> None:
    transport = _transport(session, _FakeBlobStore())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/assets", params={"project_id": str(uuid.uuid4())}, headers=_AUTH
        )

    assert response.status_code == 200
    assert response.json() == []


def test_assets_registered_in_openapi() -> None:
    schema = create_app().openapi()
    assert "/assets" in schema["paths"]
    assert "post" in schema["paths"]["/assets"]
    assert "get" in schema["paths"]["/assets"]
