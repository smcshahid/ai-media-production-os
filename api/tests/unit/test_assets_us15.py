"""US-15 SCRIPT content-read route tests."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import AssetStage, ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.assets.service import store_asset
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.storage.minio_client import ObjectNotFoundError
from app.main import create_app

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}
_SCRIPT_FOUNTAIN = b"INT. LAB - DAY\n\nAction here.\n\nDR. A\nHello.\n"


class _FakeBlobStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        import hashlib

        self.objects[key] = data
        return hashlib.md5(data).hexdigest()

    async def download_bytes(self, key: str) -> bytes:
        if key not in self.objects:
            raise ObjectNotFoundError(f"object not found: {key!r}")
        return self.objects[key]


def _transport(session: AsyncSession, blobs: _FakeBlobStore) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_minio] = lambda: blobs
    return httpx.ASGITransport(app=app)


async def _seed_script_asset(
    session: AsyncSession, blobs: _FakeBlobStore
) -> tuple[uuid.UUID, uuid.UUID]:
    project = Project(name="US-15 Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.flush()

    versions = AssetVersionRepository(session)
    stored = await store_asset(
        data=_SCRIPT_FOUNTAIN,
        stage=AssetStage.SCRIPT,
        project_id=project.id,
        blobs=blobs,
        versions=versions,
        content_type="text/plain",
        is_ai_generated=True,
        branch="ai-draft",
    )
    await session.commit()
    return project.id, stored.id


@pytest.mark.asyncio
async def test_script_content_read_returns_plain_text(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    _, asset_id = await _seed_script_asset(session, blobs)
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/{asset_id}/content", headers=_AUTH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert b"INT. LAB" in response.content


@pytest.mark.asyncio
async def test_content_read_rejects_idea_stage(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    project = Project(name="US-15 IDEA", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.flush()

    versions = AssetVersionRepository(session)
    stored = await store_asset(
        data=b"idea text",
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=blobs,
        versions=versions,
        content_type="text/plain",
    )
    await session.commit()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/{stored.id}/content", headers=_AUTH)

    assert response.status_code == 422
