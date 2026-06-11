"""US-20 lineage route tests."""

from __future__ import annotations

import uuid

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
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.assets.service import store_asset
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.lineage_edge import LineageEdge
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.approval import ApprovalRepository
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


async def _seed_with_lineage(
    session: AsyncSession,
    minio: FakeMinio,
) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    """Return (project_id, run_id, asset_ids in chain order)."""
    project = Project(name="US-20 Lineage", status=ProjectStatus.ACTIVE)
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

    idea = await store_asset(
        data=b"# Idea\n\nLineage test.",
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
    )
    story = await store_asset(
        data=b"# Story\n\nLineage test story.",
        stage=AssetStage.STORY,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/markdown",
        is_ai_generated=True,
        branch="ai-draft",
    )
    script = await store_asset(
        data=b"Title: Lineage\n\nINT. LAB - DAY\n",
        stage=AssetStage.SCRIPT,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
        is_ai_generated=True,
        branch="ai-draft",
    )

    sb_version = await versions.next_version(project.id, AssetStage.STORYBOARD)
    frame_ids: list[uuid.UUID] = []
    for idx in range(1, 5):
        png = bytes([0x89, 0x50, 0x4E, 0x47]) + bytes([idx]) * 32
        from app.domain.assets.content import build_object_key, compute_content_hash

        key = build_object_key(project.id, AssetStage.STORYBOARD, compute_content_hash(png))
        await minio.upload_bytes(key, png, "image/png")
        stored = await versions.add_version(
            project_id=project.id,
            stage=AssetStage.STORYBOARD,
            version=sb_version,
            minio_key=key,
            content_hash=compute_content_hash(png),
            is_ai_generated=True,
            branch="ai-draft",
            metadata_json={"frame_index": idx, "frame_count": 4},
        )
        frame_ids.append(stored.id)

    video = await store_asset(
        data=b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64,
        stage=AssetStage.VIDEO,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="video/mp4",
        is_ai_generated=True,
        branch="ai-draft",
    )

    for stage in (
        PipelineStage.STORY,
        PipelineStage.SCRIPT,
        PipelineStage.STORYBOARD,
        PipelineStage.VIDEO,
    ):
        await approvals.add(
            Approval(
                pipeline_run_id=run.id,
                stage=stage,
                decision=ApprovalDecision.APPROVED,
                rationale=None,
                decided_by="test",
            )
        )

    run_assets = [story.id, script.id, *frame_ids, video.id]
    for asset_id in run_assets:
        row = await session.get(AssetVersion, asset_id)
        assert row is not None
        row.pipeline_run_id = run.id

    session.add(LineageEdge(parent_id=story.id, child_id=script.id))
    for frame_id in frame_ids:
        session.add(LineageEdge(parent_id=script.id, child_id=frame_id))
        session.add(LineageEdge(parent_id=frame_id, child_id=video.id))

    await session.commit()
    chain = [idea.id, story.id, script.id, *frame_ids, video.id]
    return project.id, run.id, chain


@pytest.mark.asyncio
async def test_lineage_happy_path(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, run_id, chain = await _seed_with_lineage(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/lineage/{run_id}", headers=_AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["pipeline_run_id"] == str(run_id)
    assert body["project_id"] == str(project_id)
    assert len(body["nodes"]) == 8
    assert body["nodes"][0]["stage"] == "IDEA"
    assert body["nodes"][0]["synthetic"] is True
    assert body["nodes"][0]["parent_asset_ids"] == []
    stages = [n["stage"] for n in body["nodes"]]
    assert stages.count("STORYBOARD") == 4
    assert stages[-1] == "VIDEO"

    api_edges = {(e["parent_asset_id"], e["child_asset_id"]) for e in body["edges"]}
    assert len(api_edges) == 9
    idea_id = body["nodes"][0]["asset_id"]
    assert all(idea_id not in pair for pair in api_edges)


@pytest.mark.asyncio
async def test_lineage_edge_parity_with_repository(session: AsyncSession) -> None:
    minio = FakeMinio()
    project_id, run_id, _ = await _seed_with_lineage(session, minio)
    from app.infrastructure.db.repositories.lineage_edge import LineageEdgeRepository

    sql_edges = await LineageEdgeRepository(session).list_edges_for_run(project_id, run_id)

    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/lineage/{run_id}", headers=_AUTH)

    api_edges = {
        (e["parent_asset_id"], e["child_asset_id"]) for e in response.json()["edges"]
    }
    sql_set = {(str(p), str(c)) for p, c in sql_edges}
    assert api_edges == sql_set


@pytest.mark.asyncio
async def test_lineage_story_script_parent(session: AsyncSession) -> None:
    minio = FakeMinio()
    _, run_id, chain = await _seed_with_lineage(session, minio)
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/lineage/{run_id}", headers=_AUTH)

    script = next(n for n in response.json()["nodes"] if n["stage"] == "SCRIPT")
    assert str(chain[1]) in script["parent_asset_ids"]


@pytest.mark.asyncio
async def test_lineage_not_found(session: AsyncSession) -> None:
    minio = FakeMinio()
    transport = _transport(session, minio)
    missing = uuid.uuid4()
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/lineage/{missing}", headers=_AUTH)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_lineage_non_completed_returns_edges(session: AsyncSession) -> None:
    minio = FakeMinio()
    project = Project(name="Active", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.AWAITING_APPROVAL,
        current_stage=PipelineStage.STORY,
    )
    session.add(run)
    await session.commit()

    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/lineage/{run.id}", headers=_AUTH)
    assert response.status_code == 200
    assert response.json()["nodes"] == []


@pytest.mark.asyncio
async def test_lineage_requires_auth(session: AsyncSession) -> None:
    minio = FakeMinio()
    transport = _transport(session, minio)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/lineage/{uuid.uuid4()}")
    assert response.status_code == 401
