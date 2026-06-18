"""Phase 4 multi-scene export resolver tests."""

from __future__ import annotations

import uuid

import pytest
from aimpos_core.enums import (
    ApprovalDecision,
    AssetStage,
    PipelineRunStatus,
    PipelineStage,
    ProjectStatus,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.assets.content import build_object_key, compute_content_hash
from app.domain.assets.service import store_asset
from app.domain.export.resolver import resolve_export_files
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class FakeMinio:
    async def upload_bytes(self, key: str, data: bytes, content_type: str = "") -> str:
        return key


async def _seed_two_scene_run(session: AsyncSession, minio: FakeMinio) -> PipelineRun:
    project = Project(name="Multi-scene export", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.COMPLETED,
        current_stage=None,
        scene_count=2,
        temporal_workflow_id=f"spark-pipeline-{uuid.uuid4()}",
    )
    session.add(run)
    await session.flush()

    versions = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)

    await store_asset(
        data=b"Idea text",
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
    )
    story = await store_asset(
        data=b"# Story",
        stage=AssetStage.STORY,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/markdown",
        is_ai_generated=True,
        branch="ai-draft",
    )
    await store_asset(
        data=(
            b"INT. ROOM - DAY\n\nAction.\n\nBOB\nHi.\n\n"
            b"EXT. STREET - NIGHT\n\nMore.\n\nALICE\nHello.\n"
        ),
        stage=AssetStage.SCRIPT,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
        is_ai_generated=True,
        branch="ai-draft",
    )

    for scene_idx in (1, 2):
        sb_version = await versions.next_version(project.id, AssetStage.STORYBOARD)
        for frame_idx in range(1, 5):
            png = bytes([0x89, 0x50, 0x4E, 0x47]) + bytes([scene_idx, frame_idx]) * 16
            key = build_object_key(
                project.id, AssetStage.STORYBOARD, compute_content_hash(png)
            )
            await minio.upload_bytes(key, png, "image/png")
            await versions.add_version(
                project_id=project.id,
                stage=AssetStage.STORYBOARD,
                version=sb_version,
                minio_key=key,
                content_hash=compute_content_hash(png),
                is_ai_generated=True,
                branch="ai-draft",
                metadata_json={
                    "frame_index": frame_idx,
                    "frame_count": 4,
                    "scene_index": scene_idx,
                    "scene_count": 2,
                },
            )
        video_version = await versions.next_version(project.id, AssetStage.VIDEO)
        mp4 = b"\x00\x00\x00\x18ftypmp42" + bytes([scene_idx]) * 32
        vkey = build_object_key(project.id, AssetStage.VIDEO, compute_content_hash(mp4))
        await minio.upload_bytes(vkey, mp4, "video/mp4")
        await versions.add_version(
            project_id=project.id,
            stage=AssetStage.VIDEO,
            version=video_version,
            minio_key=vkey,
            content_hash=compute_content_hash(mp4),
            is_ai_generated=True,
            branch="ai-draft",
            metadata_json={"scene_index": scene_idx, "scene_count": 2, "source": "slideshow"},
        )

    for stage in (PipelineStage.STORY, PipelineStage.SCRIPT):
        await approvals.add(
            Approval(
                pipeline_run_id=run.id,
                stage=stage,
                decision=ApprovalDecision.APPROVED,
                decided_by="test",
            )
        )
    for scene_idx in (1, 2):
        for stage in (PipelineStage.STORYBOARD, PipelineStage.VIDEO):
            await approvals.add(
                Approval(
                    pipeline_run_id=run.id,
                    stage=stage,
                    decision=ApprovalDecision.APPROVED,
                    scene_index=scene_idx,
                    decided_by="test",
                )
            )

    await session.commit()
    return run


@pytest.mark.asyncio
async def test_resolve_export_files_two_scenes(session: AsyncSession) -> None:
    minio = FakeMinio()
    run = await _seed_two_scene_run(session, minio)
    assets = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)

    entries = await resolve_export_files(run, assets=assets, approvals=approvals)
    paths = {entry.zip_path for entry in entries}

    assert "scenes/scene_01/scene_video.mp4" in paths
    assert "scenes/scene_02/scene_video.mp4" in paths
    assert "scenes/scene_01/frames/frame_01.png" in paths
    assert "scenes/scene_02/frames/frame_04.png" in paths
    assert len(entries) == 13  # idea + story + script + 8 frames + 2 videos
