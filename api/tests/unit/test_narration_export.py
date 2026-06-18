"""Manifest v3 export tests (Phase 5)."""

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
from app.domain.export.manifest import MANIFEST_VERSION_V3, build_manifest
from app.domain.export.resolver import resolve_export_files
from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class FakeMinio:
    async def upload_bytes(self, key: str, data: bytes, content_type: str = "") -> str:
        return key


async def _seed_narrated_single_scene(session: AsyncSession, minio: FakeMinio) -> PipelineRun:
    project = Project(name="Narration export", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.COMPLETED,
        current_stage=None,
        scene_count=1,
        temporal_workflow_id=f"spark-pipeline-{uuid.uuid4()}",
    )
    session.add(run)
    await session.flush()

    versions = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)

    await store_asset(
        data=b"Idea",
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
    )
    await store_asset(
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
        data=b"INT. ROOM - DAY\n\nALICE\nHello world.\n",
        stage=AssetStage.SCRIPT,
        project_id=project.id,
        blobs=minio,
        versions=versions,
        content_type="text/plain",
        is_ai_generated=True,
        branch="ai-draft",
    )

    sb_version = await versions.next_version(project.id, AssetStage.STORYBOARD)
    for frame_idx in range(1, 5):
        png = bytes([0x89, 0x50, 0x4E, 0x47]) + bytes([frame_idx]) * 16
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
                "scene_index": 1,
                "scene_count": 1,
            },
        )

    mp4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32
    video_version = await versions.next_version(project.id, AssetStage.VIDEO)
    vkey = build_object_key(project.id, AssetStage.VIDEO, compute_content_hash(mp4))
    await minio.upload_bytes(vkey, mp4, "video/mp4")
    session.add(
        AssetVersion(
            project_id=project.id,
            pipeline_run_id=run.id,
            stage=AssetStage.VIDEO,
            version=video_version,
            minio_key=vkey,
            content_hash=compute_content_hash(mp4),
            is_ai_generated=True,
            branch="ai-draft",
            metadata_json={
                "scene_index": 1,
                "scene_count": 1,
                "has_narration": True,
                "narration_source": "espeak",
                "source": "slideshow",
            },
        )
    )

    wav = b"RIFF" + b"\x00" * 40
    narr_version = await versions.next_version(project.id, AssetStage.NARRATION)
    nkey = build_object_key(project.id, AssetStage.NARRATION, compute_content_hash(wav))
    await minio.upload_bytes(nkey, wav, "audio/wav")
    session.add(
        AssetVersion(
            project_id=project.id,
            pipeline_run_id=run.id,
            stage=AssetStage.NARRATION,
            version=narr_version,
            minio_key=nkey,
            content_hash=compute_content_hash(wav),
            is_ai_generated=True,
            branch="ai-draft",
            metadata_json={
                "scene_index": 1,
                "scene_count": 1,
                "tts_source": "espeak",
                "duration_sec": 2.5,
            },
        )
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
    for stage in (PipelineStage.STORYBOARD, PipelineStage.VIDEO):
        await approvals.add(
            Approval(
                pipeline_run_id=run.id,
                stage=stage,
                decision=ApprovalDecision.APPROVED,
                decided_by="test",
            )
        )

    await session.commit()
    return run


@pytest.mark.asyncio
async def test_export_resolver_includes_narration_wav(session: AsyncSession) -> None:
    minio = FakeMinio()
    run = await _seed_narrated_single_scene(session, minio)
    versions = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)
    entries = await resolve_export_files(run, assets=versions, approvals=approvals)
    paths = {e.zip_path for e in entries}
    assert "narration.wav" in paths
    assert "scene_video.mp4" in paths


@pytest.mark.asyncio
async def test_manifest_v3_for_narrated_run(session: AsyncSession) -> None:
    minio = FakeMinio()
    run = await _seed_narrated_single_scene(session, minio)
    versions = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)
    entries = await resolve_export_files(run, assets=versions, approvals=approvals)
    loaded = [(e, b"x" * 10) for e in entries]
    manifest = build_manifest(
        pipeline_run_id=run.id,
        project_id=run.project_id,
        exported_at=run.updated_at,
        file_entries=loaded,
        scene_count=run.scene_count,
    )
    assert manifest["manifest_version"] == MANIFEST_VERSION_V3
    assert manifest.get("narration_enabled") is True
