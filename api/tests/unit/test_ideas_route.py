"""POST /ideas route tests (US-11)."""

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
_PARAGRAPH = "A lone astronaut discovers a hidden garden on Mars."


class _FakeBlobStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        self.objects[key] = data
        return hashlib.md5(data).hexdigest()

    async def download_bytes(self, key: str) -> bytes:
        return self.objects[key]


def _transport(session: AsyncSession, blobs: _FakeBlobStore) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_minio] = lambda: blobs
    return httpx.ASGITransport(app=app)


async def _seed_project(session: AsyncSession) -> Project:
    project = Project(name="Idea Route Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()
    return project


@pytest.mark.asyncio
async def test_post_ideas_creates_idea_txt_v1(session: AsyncSession) -> None:
    project = await _seed_project(session)
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ideas",
            json={
                "project_id": str(project.id),
                "title": "Mars Garden",
                "paragraph": _PARAGRAPH,
                "style_note": "cinematic sci-fi",
            },
            headers=_AUTH,
        )

    assert response.status_code == 201
    body = response.json()
    assert body["stage"] == "IDEA"
    assert body["version"] == 1
    assert body["metadata_json"] == {"style_note": "cinematic sci-fi"}
    assert len(blobs.objects) == 1
    blob = next(iter(blobs.objects.values()))
    assert blob.decode("utf-8") == f"Mars Garden\n\n{_PARAGRAPH}"


@pytest.mark.asyncio
async def test_post_ideas_lists_on_get_assets(session: AsyncSession) -> None:
    project = await _seed_project(session)
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        create = await client.post(
            "/ideas",
            json={
                "project_id": str(project.id),
                "title": "Mars Garden",
                "paragraph": _PARAGRAPH,
            },
            headers=_AUTH,
        )
        assert create.status_code == 201
        listed = await client.get(f"/assets?project_id={project.id}", headers=_AUTH)

    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["stage"] == "IDEA"


@pytest.mark.asyncio
async def test_post_ideas_unknown_project_returns_404(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ideas",
            json={
                "project_id": str(uuid.uuid4()),
                "title": "Mars Garden",
                "paragraph": _PARAGRAPH,
            },
            headers=_AUTH,
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_ideas_short_paragraph_returns_422(session: AsyncSession) -> None:
    project = await _seed_project(session)
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ideas",
            json={
                "project_id": str(project.id),
                "title": "Mars Garden",
                "paragraph": "too short",
            },
            headers=_AUTH,
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_ideas_missing_title_returns_422(session: AsyncSession) -> None:
    project = await _seed_project(session)
    blobs = _FakeBlobStore()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ideas",
            json={
                "project_id": str(project.id),
                "title": "   ",
                "paragraph": _PARAGRAPH,
            },
            headers=_AUTH,
        )

    assert response.status_code == 422
