"""Manifest v4 episode export tests (Phase 6)."""

from __future__ import annotations

import uuid

import pytest
from aimpos_core.enums import (
    ApprovalDecision,
    AssetStage,
    EpisodeStatus,
    PipelineRunStatus,
    PipelineStage,
    ProjectStatus,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.assets.content import build_object_key, compute_content_hash
from app.domain.assets.service import store_asset
from app.domain.export.manifest import MANIFEST_VERSION_V4, build_manifest
from app.domain.export.resolver import resolve_export_files
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.episode import Episode
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class FakeMinio:
    async def upload_bytes(self, key: str, data: bytes, content_type: str = "") -> str:
        return key


async def _seed_episode_narrated_run(
    session: AsyncSession,
    minio: FakeMinio,
    *,
    scene_count: int = 1,
) -> tuple[PipelineRun, Episode]:
    project = Project(name="Episode export", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    episode = Episode(
        project_id=project.id,
        episode_number=1,
        title="Pilot Episode",
        status=EpisodeStatus.COMPLETED,
    )
    session.add(episode)
    await session.flush()

    run = PipelineRun(
        project_id=project.id,
        episode_id=episode.id,
        status=PipelineRunStatus.COMPLETED,
        current_stage=None,
        scene_count=scene_count,
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

    for stage, data in (
        (AssetStage.STORY, b"# Story"),
        (AssetStage.SCRIPT, b"INT. ROOM - DAY\n\nALICE\nHello.\n"),
    ):
        version = await versions.next_version(project.id, stage)
        key = build_object_key(project.id, stage, compute_content_hash(data))
        await minio.upload_bytes(key, data, "text/plain")
        session.add(
            AssetVersion(
                project_id=project.id,
                pipeline_run_id=run.id,
                stage=stage,
                version=version,
                minio_key=key,
                content_hash=compute_content_hash(data),
                is_ai_generated=True,
                branch="ai-draft",
                metadata_json={"episode_number": episode.episode_number},
            )
        )

    for scene_idx in range(1, scene_count + 1):
        sb_version = await versions.next_version(project.id, AssetStage.STORYBOARD)
        for frame_idx in range(1, 5):
            png = bytes([0x89, 0x50, 0x4E, 0x47]) + bytes([frame_idx, scene_idx]) * 8
            key = build_object_key(
                project.id, AssetStage.STORYBOARD, compute_content_hash(png)
            )
            await minio.upload_bytes(key, png, "image/png")
            session.add(
                AssetVersion(
                    project_id=project.id,
                    pipeline_run_id=run.id,
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
                        "scene_count": scene_count,
                        "episode_number": episode.episode_number,
                    },
                )
            )

        mp4 = b"\x00\x00\x00\x18ftypmp42" + bytes([scene_idx]) * 32
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
                    "scene_index": scene_idx,
                    "scene_count": scene_count,
                    "episode_number": episode.episode_number,
                    "has_narration": True,
                    "narration_source": "espeak",
                },
            )
        )

        wav = b"RIFF" + bytes([scene_idx]) * 40
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
                    "scene_index": scene_idx,
                    "scene_count": scene_count,
                    "episode_number": episode.episode_number,
                    "tts_source": "espeak",
                    "duration_sec": 2.0,
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
    for scene_idx in range(1, scene_count + 1):
        for stage in (PipelineStage.STORYBOARD, PipelineStage.VIDEO):
            await approvals.add(
                Approval(
                    pipeline_run_id=run.id,
                    stage=stage,
                    decision=ApprovalDecision.APPROVED,
                    decided_by="test",
                    scene_index=scene_idx if scene_count > 1 else None,
                )
            )

    await session.commit()
    return run, episode


@pytest.mark.asyncio
async def test_export_resolver_episode_v4_paths(session: AsyncSession) -> None:
    minio = FakeMinio()
    run, episode = await _seed_episode_narrated_run(session, minio, scene_count=1)
    versions = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)
    entries = await resolve_export_files(
        run,
        assets=versions,
        approvals=approvals,
        episode_number=episode.episode_number,
    )
    paths = {e.zip_path for e in entries}
    assert "idea.txt" in paths
    assert "episodes/episode_01/story.md" in paths
    assert "episodes/episode_01/scene_video.mp4" in paths
    assert "episodes/episode_01/narration.wav" in paths


@pytest.mark.asyncio
async def test_manifest_v4_for_episode_run(session: AsyncSession) -> None:
    minio = FakeMinio()
    run, episode = await _seed_episode_narrated_run(session, minio, scene_count=3)
    versions = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)
    entries = await resolve_export_files(
        run,
        assets=versions,
        approvals=approvals,
        episode_number=episode.episode_number,
    )
    loaded = [(e, b"x" * 10) for e in entries]
    manifest = build_manifest(
        pipeline_run_id=run.id,
        project_id=run.project_id,
        exported_at=run.updated_at,
        file_entries=loaded,
        scene_count=run.scene_count,
        episode_id=episode.id,
        episode_number=episode.episode_number,
    )
    assert manifest["manifest_version"] == MANIFEST_VERSION_V4
    assert manifest["episode_number"] == 1
    assert manifest["narration_enabled"] is True
    assert manifest["scene_count"] == 3
    assert any(
        f["path"].startswith("episodes/episode_01/scenes/scene_03/")
        for f in manifest["files"]
    )
