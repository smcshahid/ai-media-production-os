"""Resolve approved assets for export (US-19 D-52)."""

from __future__ import annotations

import uuid

from aimpos_core.enums import AssetStage, PipelineStage

from app.domain.export.types import ExportFileEntry
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository

_STORYBOARD_FRAME_COUNT = 4


class ExportAssetResolutionError(Exception):
    """COMPLETED run is missing expected approved assets."""


async def resolve_export_files(
    run: PipelineRun,
    *,
    assets: AssetVersionRepository,
    approvals: ApprovalRepository,
) -> list[ExportFileEntry]:
    """Map approved assets at latest versions to deterministic ZIP paths."""
    project_id = run.project_id
    run_id = run.id
    entries: list[ExportFileEntry] = []

    idea = await assets.get_at_version(project_id, AssetStage.IDEA, 1)
    if idea is None:
        raise ExportAssetResolutionError("missing IDEA asset")
    entries.append(
        ExportFileEntry(
            asset=idea,
            zip_path="idea.txt",
            approval_at=None,
        )
    )

    for stage, path in (
        (AssetStage.STORY, "story.md"),
        (AssetStage.SCRIPT, "script.fountain"),
    ):
        version = await assets.max_version(project_id, stage)
        if version < 1:
            raise ExportAssetResolutionError(f"missing {stage.value} asset")
        row = await assets.get_at_version(project_id, stage, version)
        if row is None:
            raise ExportAssetResolutionError(f"missing {stage.value} asset at version {version}")
        approval = await approvals.latest_approved_for_stage(run_id, PipelineStage(stage.value))
        entries.append(
            ExportFileEntry(
                asset=row,
                zip_path=path,
                approval_at=approval.created_at if approval else None,
            )
        )

    sb_version = await assets.max_version(project_id, AssetStage.STORYBOARD)
    if sb_version < 1:
        raise ExportAssetResolutionError("missing STORYBOARD batch")
    frames = await assets.list_storyboard_batch(project_id, sb_version)
    if len(frames) != _STORYBOARD_FRAME_COUNT:
        raise ExportAssetResolutionError(
            f"expected {_STORYBOARD_FRAME_COUNT} storyboard frames, got {len(frames)}"
        )
    sb_approval = await approvals.latest_approved_for_stage(
        run_id, PipelineStage.STORYBOARD
    )
    for frame in frames:
        idx = int((frame.metadata_json or {}).get("frame_index", 0))
        entries.append(
            ExportFileEntry(
                asset=frame,
                zip_path=f"frames/frame_{idx:02d}.png",
                approval_at=sb_approval.created_at if sb_approval else None,
            )
        )

    video_version = await assets.max_version(project_id, AssetStage.VIDEO)
    if video_version < 1:
        raise ExportAssetResolutionError("missing VIDEO asset")
    video = await assets.get_at_version(project_id, AssetStage.VIDEO, video_version)
    if video is None:
        raise ExportAssetResolutionError("missing VIDEO asset row")
    video_approval = await approvals.latest_approved_for_stage(run_id, PipelineStage.VIDEO)
    entries.append(
        ExportFileEntry(
            asset=video,
            zip_path="scene_video.mp4",
            approval_at=video_approval.created_at if video_approval else None,
        )
    )

    return entries
