"""US-19 export route tests."""

from __future__ import annotations

import io
import json
import uuid
import zipfile

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import (
    ApprovalDecision,
    AssetStage,
    PipelineRunStatus,
    PipelineStage,
    ProjectStatus,
)
from aimpos_core.events import AuditEventType
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.assets.service import store_asset
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.audit_event import AuditEventRepository
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


async def _seed_completed_run(
    session: AsyncSession,
    minio: FakeMinio,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Return (project_id, run_id) with full COMPLETED asset set."""
    project = Project(name="US-19 Export", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.COMPLETED,
        current_stage=None,
        temporal_workflow_id=f"spark-pipeline-{uuid.uuid4()}",
    )
    session.add(run)
    await session.flush()

    versions = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)

    await store_asset(
        data=b"# Idea\n\nExport test idea.",
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
    )
    story = await store_asset(
        data=b"# Story\n\nExport test story.",
        stage=AssetStage.STORY,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/markdown",
        is_ai_generated=True,
        branch="ai-draft",
    )
    script = await store_asset(
        data=b"Title: Export Test\n\nINT. LAB - DAY\n",
        stage=AssetStage.SCRIPT,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
        is_ai_generated=True,
        branch="ai-draft",
    )
    sb_version = await versions.next_version(project.id, AssetStage.STORYBOARD)
    for idx in range(1, 5):
        png = bytes([0x89, 0x50, 0x4E, 0x47]) + bytes([idx]) * 32
        from app.domain.assets.content import build_object_key, compute_content_hash

        key = build_object_key(project.id, AssetStage.STORYBOARD, compute_content_hash(png))
        await minio.upload_bytes(key, png, "image/png")
        await versions.add_version(
            project_id=project.id,
            stage=AssetStage.STORYBOARD,
            version=sb_version,
            minio_key=key,
            content_hash=compute_content_hash(png),
            is_ai_generated=True,
            branch="ai-draft",
            metadata_json={"frame_index": idx, "frame_count": 4},
        )
    video = await store_asset(
        data=b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64,
        stage=AssetStage.VIDEO,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="video/mp4",
        is_ai_generated=True,
        branch="ai-draft",
        metadata_json={"duration_sec": 20.0, "source": "slideshow"},
    )

    for stage in (PipelineStage.STORY, PipelineStage.SCRIPT, PipelineStage.STORYBOARD, PipelineStage.VIDEO):
        await approvals.add(
            Approval(
                pipeline_run_id=run.id,
                stage=stage,
                decision=ApprovalDecision.APPROVED,
                rationale=None,
                decided_by="test",
            )
        )

    await session.commit()
    return project.id, run.id


@pytest.mark.asyncio
async def test_export_happy_path(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, run_id = await _seed_completed_run(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/export/{run_id}", headers=_AUTH)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.content[:2] == b"PK"

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        names = zf.namelist()
        assert names[0] == "manifest.json"
        assert len(names) == 9
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["manifest_version"] == "1"
        assert manifest["pipeline_run_id"] == str(run_id)
        assert manifest["project_id"] == str(project_id)
        assert len(manifest["files"]) == 8

    events = await AuditEventRepository(session).list_for_run(run_id)
    exported = [e for e in events if e.event_type == AuditEventType.BUNDLE_EXPORTED]
    assert len(exported) == 1
    assert exported[0].payload["file_count"] == 8


@pytest.mark.asyncio
async def test_export_manifest_hashes_match(session: AsyncSession) -> None:
    minio = FakeMinio()
    _, run_id = await _seed_completed_run(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/export/{run_id}", headers=_AUTH)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        for file_meta in manifest["files"]:
            data = zf.read(file_meta["path"])
            from app.domain.assets.content import compute_content_hash

            assert compute_content_hash(data) == file_meta["content_hash"]


@pytest.mark.asyncio
async def test_export_not_found(session: AsyncSession) -> None:
    minio = FakeMinio()
    transport = _transport(session, minio)
    missing = uuid.uuid4()
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/export/{missing}", headers=_AUTH)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_export_not_completed(session: AsyncSession) -> None:
    minio = FakeMinio()
    project = Project(name="Active", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.AWAITING_APPROVAL,
        current_stage=PipelineStage.VIDEO,
    )
    session.add(run)
    await session.commit()

    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/export/{run.id}", headers=_AUTH)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_export_requires_auth(session: AsyncSession) -> None:
    minio = FakeMinio()
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/export/{uuid.uuid4()}")
    assert response.status_code == 401
