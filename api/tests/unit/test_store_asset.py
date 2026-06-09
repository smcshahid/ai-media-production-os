"""store_asset service tests (T-05-03) with a fake blob store + real repository."""

from __future__ import annotations

import hashlib

import pytest
from aimpos_core.enums import AssetStage, ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.assets.content import build_object_key, compute_content_hash
from app.domain.assets.service import StoredAsset, store_asset
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class _FakeBlobStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        self.objects[key] = data
        return hashlib.md5(data).hexdigest()  # mimics MinIO single-PUT ETag

    async def download_bytes(self, key: str) -> bytes:
        return self.objects[key]


async def _make_project(session: AsyncSession) -> Project:
    project = Project(name="Asset Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    return project


@pytest.mark.asyncio
async def test_store_asset_hashes_uploads_and_records(session: AsyncSession) -> None:
    project = await _make_project(session)
    blobs = _FakeBlobStore()
    data = b"idea bytes"

    stored = await store_asset(
        data=data,
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=blobs,
        versions=AssetVersionRepository(session),
    )

    assert isinstance(stored, StoredAsset)
    assert stored.content_hash == compute_content_hash(data)
    assert stored.minio_key == build_object_key(project.id, AssetStage.IDEA, stored.content_hash)
    assert stored.version == 1
    assert blobs.objects[stored.minio_key] == data


@pytest.mark.asyncio
async def test_store_asset_dedup_blob_new_version(session: AsyncSession) -> None:
    project = await _make_project(session)
    blobs = _FakeBlobStore()
    versions = AssetVersionRepository(session)
    data = b"same content"

    first = await store_asset(
        data=data, stage=AssetStage.STORY, project_id=project.id, blobs=blobs, versions=versions
    )
    second = await store_asset(
        data=data, stage=AssetStage.STORY, project_id=project.id, blobs=blobs, versions=versions
    )

    assert (first.version, second.version) == (1, 2)
    assert first.content_hash == second.content_hash
    assert first.minio_key == second.minio_key  # blob dedup: one key
    assert len(blobs.objects) == 1
    assert len(await versions.list_for_project(project.id)) == 2


@pytest.mark.asyncio
async def test_store_asset_passes_through_flags(session: AsyncSession) -> None:
    project = await _make_project(session)

    stored = await store_asset(
        data=b"ai output",
        stage=AssetStage.SCRIPT,
        project_id=project.id,
        blobs=_FakeBlobStore(),
        versions=AssetVersionRepository(session),
        is_ai_generated=True,
        branch="experiment",
    )

    assert stored.is_ai_generated is True
    assert stored.branch == "experiment"
