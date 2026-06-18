"""Resolve approved assets for export (US-19 D-52 / Phase 4 v2 / Phase 6 v4)."""

from __future__ import annotations

import uuid

from aimpos_core.enums import AssetStage, PipelineStage
from aimpos_core.episode import episode_zip_prefix

from app.domain.export.types import ExportFileEntry
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository

_STORYBOARD_FRAME_COUNT = 4


class ExportAssetResolutionError(Exception):
    """COMPLETED run is missing expected approved assets."""


def _scene_count_for_run(run: PipelineRun) -> int:
    if run.scene_count is not None and run.scene_count >= 1:
        return int(run.scene_count)
    return 1


def _episode_prefix(episode_number: int | None) -> str:
    if episode_number is None:
        return ""
    return episode_zip_prefix(episode_number)


def _storyboard_zip_path(
    scene_index: int,
    frame_index: int,
    *,
    multi_scene: bool,
    episode_prefix: str,
) -> str:
    if episode_prefix and multi_scene:
        return (
            f"{episode_prefix}/scenes/scene_{scene_index:02d}/"
            f"frames/frame_{frame_index:02d}.png"
        )
    if episode_prefix:
        return f"{episode_prefix}/frames/frame_{frame_index:02d}.png"
    if multi_scene:
        return f"scenes/scene_{scene_index:02d}/frames/frame_{frame_index:02d}.png"
    return f"frames/frame_{frame_index:02d}.png"


def _video_zip_path(
    scene_index: int,
    *,
    multi_scene: bool,
    episode_prefix: str,
) -> str:
    if episode_prefix and multi_scene:
        return f"{episode_prefix}/scenes/scene_{scene_index:02d}/scene_video.mp4"
    if episode_prefix:
        return f"{episode_prefix}/scene_video.mp4"
    if multi_scene:
        return f"scenes/scene_{scene_index:02d}/scene_video.mp4"
    return "scene_video.mp4"


def _narration_zip_path(
    scene_index: int,
    *,
    multi_scene: bool,
    episode_prefix: str,
) -> str:
    if episode_prefix and multi_scene:
        return f"{episode_prefix}/scenes/scene_{scene_index:02d}/narration.wav"
    if episode_prefix:
        return f"{episode_prefix}/narration.wav"
    if multi_scene:
        return f"scenes/scene_{scene_index:02d}/narration.wav"
    return "narration.wav"


async def resolve_export_files(
    run: PipelineRun,
    *,
    assets: AssetVersionRepository,
    approvals: ApprovalRepository,
    episode_number: int | None = None,
) -> list[ExportFileEntry]:
    """Map approved assets at latest versions to deterministic ZIP paths."""
    project_id = run.project_id
    run_id = run.id
    entries: list[ExportFileEntry] = []
    scene_count = _scene_count_for_run(run)
    multi_scene = scene_count > 1
    episode_prefix = _episode_prefix(episode_number)
    episode_scoped = episode_number is not None

    idea = await assets.get_at_version(project_id, AssetStage.IDEA, 1)
    if idea is None:
        raise ExportAssetResolutionError("missing IDEA asset")
    idea_path = "idea.txt"
    entries.append(
        ExportFileEntry(
            asset=idea,
            zip_path=idea_path,
            approval_at=None,
        )
    )

    for stage, path in (
        (AssetStage.STORY, "story.md"),
        (AssetStage.SCRIPT, "script.fountain"),
    ):
        if episode_scoped:
            row = await assets.latest_for_run(project_id, stage, run_id)
        else:
            version = await assets.max_version(project_id, stage)
            if version < 1:
                raise ExportAssetResolutionError(f"missing {stage.value} asset")
            row = await assets.get_at_version(project_id, stage, version)
        if row is None:
            raise ExportAssetResolutionError(f"missing {stage.value} asset for run")
        zip_path = path if not episode_prefix else f"{episode_prefix}/{path}"
        approval = await approvals.latest_approved_for_stage(run_id, PipelineStage(stage.value))
        entries.append(
            ExportFileEntry(
                asset=row,
                zip_path=zip_path,
                approval_at=approval.created_at if approval else None,
            )
        )

    for scene_idx in range(1, scene_count + 1):
        frames = await assets.list_storyboard_batch_for_scene(project_id, scene_idx)
        if episode_scoped:
            frames = [f for f in frames if f.pipeline_run_id == run_id]
        if len(frames) != _STORYBOARD_FRAME_COUNT:
            raise ExportAssetResolutionError(
                f"expected {_STORYBOARD_FRAME_COUNT} storyboard frames for scene "
                f"{scene_idx}, got {len(frames)}"
            )
        sb_approval = await approvals.latest_approved_for_stage(
            run_id, PipelineStage.STORYBOARD, scene_index=scene_idx if multi_scene else None
        )
        for frame in frames:
            idx = int((frame.metadata_json or {}).get("frame_index", 0))
            entries.append(
                ExportFileEntry(
                    asset=frame,
                    zip_path=_storyboard_zip_path(
                        scene_idx,
                        idx,
                        multi_scene=multi_scene,
                        episode_prefix=episode_prefix,
                    ),
                    approval_at=sb_approval.created_at if sb_approval else None,
                )
            )

        video = await assets.latest_video_for_scene(
            project_id, scene_idx, pipeline_run_id=run_id
        )
        if video is None:
            raise ExportAssetResolutionError(f"missing VIDEO asset for scene {scene_idx}")
        video_meta = video.metadata_json or {}
        video_approval = await approvals.latest_approved_for_stage(
            run_id, PipelineStage.VIDEO, scene_index=scene_idx if multi_scene else None
        )
        entries.append(
            ExportFileEntry(
                asset=video,
                zip_path=_video_zip_path(
                    scene_idx, multi_scene=multi_scene, episode_prefix=episode_prefix
                ),
                approval_at=video_approval.created_at if video_approval else None,
            )
        )

        if video_meta.get("has_narration") is True:
            narration = await assets.latest_narration_for_scene(
                project_id, scene_idx, pipeline_run_id=run_id
            )
            if narration is not None:
                entries.append(
                    ExportFileEntry(
                        asset=narration,
                        zip_path=_narration_zip_path(
                            scene_idx,
                            multi_scene=multi_scene,
                            episode_prefix=episode_prefix,
                        ),
                        approval_at=video_approval.created_at if video_approval else None,
                    )
                )

    return entries
