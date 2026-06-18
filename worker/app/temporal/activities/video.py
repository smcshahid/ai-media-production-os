"""VIDEO stage slideshow / i2v activity (US-18 / Phase 4)."""

from __future__ import annotations

import uuid

from aimpos_config import get_settings
from aimpos_core.events import AuditEventType
from temporalio import activity

from app.agents.narration.constants import SOURCE_NONE
from app.agents.narration.pipeline import NarrationResult, apply_scene_narration
from app.agents.video.constants import (
    AGENT_ID,
    SOURCE_COMFYUI_I2V,
    SOURCE_SLIDESHOW,
    VIDEO_BRANCH,
)
from app.agents.video.slideshow import SlideshowRenderError, render_slideshow_mp4
from app.agents.video.validate import VideoValidationError, validate_video_mp4
from app.infrastructure.gpu.sequencer import (
    GpuSequencerError,
    unload_ollama_before_comfyui,
)
from app.temporal.activities.pipeline_status import sync_pipeline_status
from app.tools.assets import (
    ApprovedStoryboardNotFoundError,
    AssetStoreError,
    VideoStoreError,
    fetch_approved_storyboard_batch,
    fetch_latest_video_rejection_rationale,
    store_video_asset,
)
from app.tools.audit import append_audit_event
from app.tools.pipeline_run import _read_run_scene_count
from app.tools.video_i2v import VideoI2VError, try_comfyui_i2v


@activity.defn(name="run_video_agent")
async def run_video_agent(
    project_id: str,
    run_id: str,
    rejection_note: str = "",
    scene_index: int = 1,
) -> str:
    """Generate one MP4 from approved storyboard batch for a scene (D-48 / D-76)."""
    settings = get_settings()
    project_uuid = uuid.UUID(project_id)
    run_uuid = uuid.UUID(run_id)
    scene_count = _read_run_scene_count(settings, pipeline_run_id=run_uuid)

    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.STAGE_STARTED,
        payload={
            "stage": "VIDEO",
            "agent": AGENT_ID,
            "scene_index": scene_index,
            "scene_count": scene_count,
        },
    )

    try:
        batch = fetch_approved_storyboard_batch(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            scene_index=scene_index,
        )
        png_frames = [frame.png_bytes for frame in batch.frames]
        frame_ids = [frame.asset_version_id for frame in batch.frames]

        db_rationale = fetch_latest_video_rejection_rationale(
            settings, pipeline_run_id=run_uuid, scene_index=scene_index
        )
        effective_note = (rejection_note or "").strip() or (db_rationale or "")

        source = SOURCE_SLIDESHOW
        fallback_from: str | None = None
        fallback_reason: str | None = None
        mp4_bytes: bytes

        try:
            if getattr(settings, "video_i2v_enabled", False):
                unload_ollama_before_comfyui(settings)
            candidate = try_comfyui_i2v(settings, png_frames)
            probe = validate_video_mp4(candidate)
            mp4_bytes = candidate
            source = SOURCE_COMFYUI_I2V
        except (VideoI2VError, VideoValidationError, GpuSequencerError) as exc:
            activity.logger.warning(
                "video_i2v_failed",
                extra={
                    "project_id": project_id,
                    "run_id": run_id,
                    "scene_index": scene_index,
                    "error": str(exc),
                },
            )
            fallback_from = SOURCE_COMFYUI_I2V
            fallback_reason = str(exc)[:500]
            mp4_bytes, probe = render_slideshow_mp4(png_frames)
            source = SOURCE_SLIDESHOW

        metadata = {
            "duration_sec": round(probe.duration_sec, 3),
            "width": probe.width,
            "height": probe.height,
            "codec": probe.codec,
            "source": source,
            "frame_count": len(frame_ids),
            "fps": (
                int(getattr(settings, "video_i2v_fps", 24))
                if source == SOURCE_COMFYUI_I2V
                else 24
            ),
            "file_size_bytes": len(mp4_bytes),
            "logical_filename": f"scene_{scene_index:02d}_video.mp4",
        }
        if effective_note:
            metadata["rejection_note_used"] = effective_note[:500]
        if fallback_from:
            metadata["fallback_from"] = fallback_from
            metadata["fallback_reason"] = fallback_reason

        silent_mp4_bytes = mp4_bytes
        narration = apply_scene_narration(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            scene_index=scene_index,
            scene_count=scene_count,
            silent_mp4_bytes=silent_mp4_bytes,
        )
        mp4_bytes = narration.mp4_bytes
        if narration.narration_applied:
            try:
                probe = validate_video_mp4(mp4_bytes)
                metadata["duration_sec"] = round(probe.duration_sec, 3)
            except VideoValidationError:
                activity.logger.warning(
                    "narration_mux_validation_failed",
                    extra={
                        "project_id": project_id,
                        "run_id": run_id,
                        "scene_index": scene_index,
                    },
                )
                mp4_bytes = silent_mp4_bytes
                narration = NarrationResult(
                    mp4_bytes=silent_mp4_bytes,
                    narration_applied=False,
                    narration_source=SOURCE_NONE,
                    narration_text="",
                    narration_duration_sec=None,
                    narration_asset_id=None,
                )
        metadata["file_size_bytes"] = len(mp4_bytes)
        metadata["has_narration"] = narration.narration_applied
        metadata["narration_source"] = narration.narration_source
        if narration.narration_duration_sec is not None:
            metadata["narration_duration_sec"] = narration.narration_duration_sec
        if narration.narration_asset_id:
            metadata["narration_asset_id"] = narration.narration_asset_id

        stored = store_video_asset(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            mp4_bytes=mp4_bytes,
            frame_parent_ids=frame_ids,
            metadata=metadata,
            branch=VIDEO_BRANCH,
            scene_index=scene_index,
            scene_count=scene_count,
        )
    except (
        ApprovedStoryboardNotFoundError,
        AssetStoreError,
        VideoStoreError,
        SlideshowRenderError,
        VideoValidationError,
        RuntimeError,
    ) as exc:
        await _mark_video_failed(project_uuid, run_uuid, exc, scene_index)
        raise
    except Exception as exc:
        await _mark_video_failed(project_uuid, run_uuid, exc, scene_index)
        raise

    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.AGENT_TASK_COMPLETED,
        payload={
            "agent": AGENT_ID,
            "stage": "VIDEO",
            "source": source,
            "version": stored.version,
            "duration_sec": metadata["duration_sec"],
            "rejection_note": effective_note or None,
            "scene_index": scene_index,
            "scene_count": scene_count,
            "has_narration": narration.narration_applied,
            "narration_source": narration.narration_source,
        },
    )
    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.ASSET_STORED,
        payload={
            "stage": "VIDEO",
            "branch": VIDEO_BRANCH,
            "content_hash": stored.content_hash,
            "version": stored.version,
            "source": source,
            "scene_index": scene_index,
            "has_narration": narration.narration_applied,
        },
    )

    activity.logger.info(
        "video_agent_completed",
        extra={
            "project_id": project_id,
            "run_id": run_id,
            "scene_index": scene_index,
            "asset_version_id": str(stored.asset_version_id),
            "source": source,
            "video_method": source,
        },
    )
    return str(stored.asset_version_id)


async def _mark_video_failed(
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    exc: Exception,
    scene_index: int,
) -> None:
    settings = get_settings()
    append_audit_event(
        settings,
        project_id=project_id,
        pipeline_run_id=run_id,
        event_type=AuditEventType.PIPELINE_FAILED,
        payload={
            "stage": "VIDEO",
            "error": str(exc),
            "agent": AGENT_ID,
            "scene_index": scene_index,
        },
    )
    await sync_pipeline_status(str(run_id), "FAILED", "VIDEO", scene_index)
