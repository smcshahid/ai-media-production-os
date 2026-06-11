"""US-22 asset history route tests."""

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


class FakeMinio:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    async def upload_bytes(self, key: str, data: bytes, content_type: str = "") -> str:
        self._objects[key] = data
        return key

    async def download_bytes(self, key: str) -> bytes:
        return self._objects[key]


def _transport(session: AsyncSession, minio: FakeMinio) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_minio] = lambda: minio
    return httpx.ASGITransport(app=app)


async def _seed_history_project(
    session: AsyncSession,
    minio: FakeMinio,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """Return (project_id, run_id, latest_story_id)."""
    project = Project(name="US-22 History", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run_id = uuid.uuid4()
    versions = AssetVersionRepository(session)

    await store_asset(
        data=b"Idea text",
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
    )
    story_v1 = await store_asset(
        data=b"# Story v1",
        stage=AssetStage.STORY,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/markdown",
        is_ai_generated=True,
        branch="ai-draft",
    )
    story_v2 = await store_asset(
        data=b"# Story v2 human",
        stage=AssetStage.STORY,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/markdown",
        is_ai_generated=False,
        branch="human-edit",
    )
    await store_asset(
        data=b"Title: T\n\nINT. X - DAY\n",
        stage=AssetStage.SCRIPT,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
        is_ai_generated=True,
        branch="ai-draft",
    )

    for batch_version in (1, 2):
        for idx in range(1, 5):
            png = bytes([0x89, 0x50, 0x4E, 0x47, batch_version, idx]) + b"\x00" * 28
            from app.domain.assets.content import build_object_key, compute_content_hash

            key = build_object_key(project.id, AssetStage.STORYBOARD, compute_content_hash(png))
            await minio.upload_bytes(key, png, "image/png")
            await versions.add_version(
                project_id=project.id,
                stage=AssetStage.STORYBOARD,
                version=batch_version,
                minio_key=key,
                content_hash=compute_content_hash(png),
                is_ai_generated=True,
                branch="ai-draft",
                metadata_json={"frame_index": idx, "frame_count": 4},
            )

    from app.infrastructure.db.models.asset_version import AssetVersion

    for asset_id in (story_v1.id, story_v2.id):
        row = await session.get(AssetVersion, asset_id)
        assert row is not None
        row.pipeline_run_id = run_id

    await session.commit()
    return project.id, run_id, story_v2.id


@pytest.mark.asyncio
async def test_asset_history_grouped_and_sorted(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, _, latest_story_id = await _seed_history_project(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/assets/history?project_id={project_id}",
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == str(project_id)
    stage_names = [s["stage"] for s in body["stages"]]
    assert stage_names == ["IDEA", "STORY", "SCRIPT", "STORYBOARD"]

    story = next(s for s in body["stages"] if s["stage"] == "STORY")
    assert len(story["versions"]) == 2
    assert story["versions"][0]["version"] == 2
    assert story["versions"][0]["asset_id"] == str(latest_story_id)
    assert story["versions"][0]["branch"] == "human-edit"

    sb = next(s for s in body["stages"] if s["stage"] == "STORYBOARD")
    assert len(sb["versions"]) == 8
    assert sb["versions"][0]["version"] == 2
    assert sb["versions"][0]["metadata"]["frame_index"] == 1
    assert sb["versions"][3]["metadata"]["frame_index"] == 4
    assert sb["versions"][4]["version"] == 1


@pytest.mark.asyncio
async def test_asset_history_sql_parity(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, _, _ = await _seed_history_project(session, minio)
    repo = AssetVersionRepository(session)
    sql_count = await repo.count_for_project(project_id)

    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/assets/history?project_id={project_id}",
            headers=_AUTH,
        )

    api_count = sum(len(s["versions"]) for s in response.json()["stages"])
    assert api_count == sql_count


@pytest.mark.asyncio
async def test_asset_history_stage_filter(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, _, _ = await _seed_history_project(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/assets/history?project_id={project_id}&stage=STORY",
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["stages"]) == 1
    assert body["stages"][0]["stage"] == "STORY"
    assert len(body["stages"][0]["versions"]) == 2


@pytest.mark.asyncio
async def test_asset_history_run_filter_includes_idea(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, run_id, _ = await _seed_history_project(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/assets/history?project_id={project_id}&pipeline_run_id={run_id}",
            headers=_AUTH,
        )

    body = response.json()
    stage_names = [s["stage"] for s in body["stages"]]
    assert "IDEA" in stage_names
    assert "STORY" in stage_names
    story_count = next(s for s in body["stages"] if s["stage"] == "STORY")["versions"]
    assert len(story_count) == 2


@pytest.mark.asyncio
async def test_asset_history_not_found(session: AsyncSession) -> None:
    minio = FakeMinio()
    transport = _transport(session, minio)
    missing = uuid.uuid4()
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/assets/history?project_id={missing}",
            headers=_AUTH,
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_asset_history_requires_auth(session: AsyncSession) -> None:
    minio = FakeMinio()
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/history?project_id={uuid.uuid4()}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_asset_history_content_read_reuse(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, _, latest_story_id = await _seed_history_project(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        content = await client.get(f"/assets/{latest_story_id}/content", headers=_AUTH)
    assert content.status_code == 200
    assert b"Story v2" in content.content
