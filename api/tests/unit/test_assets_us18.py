"""US-18 VIDEO content-read route tests."""

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
from app.main import create_app

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}
_MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


class FakeMinio:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    async def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        self._objects[key] = data
        return key

    async def download_bytes(self, key: str) -> bytes:
        return self._objects[key]


def _transport(session: AsyncSession, minio: FakeMinio) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_minio] = lambda: minio
    return httpx.ASGITransport(app=app)


@pytest.mark.asyncio
async def test_video_content_read_returns_mp4(session: AsyncSession) -> None:
    project = Project(name="US-18", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()

    minio = FakeMinio()
    stored = await store_asset(
        data=_MP4,
        stage=AssetStage.VIDEO,
        project_id=project.id,
        blobs=minio,
        versions=AssetVersionRepository(session),
        content_type="video/mp4",
        metadata_json={
            "duration_sec": 20.0,
            "width": 854,
            "height": 480,
            "source": "slideshow",
        },
    )
    await session.commit()
    asset_id = stored.id

    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/{asset_id}/content", headers=_AUTH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("video/mp4")
    assert response.content[4:8] == b"ftyp"
