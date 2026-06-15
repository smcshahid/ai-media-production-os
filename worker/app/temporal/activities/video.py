"""VIDEO stage slideshow / i2v activity (US-18)."""

from __future__ import annotations

import uuid

from aimpos_config import get_settings
from aimpos_core.events import AuditEventType
from temporalio import activity

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
from app.tools.video_i2v import VideoI2VError, try_comfyui_i2v


@activity.defn(name="run_video_agent")
async def run_video_agent(
    project_id: str, run_id: str, rejection_note: str = ""
) -> str:
    """Generate one MP4 from approved storyboard batch (D-48 / D-49)."""
    settings = get_settings()
    project_uuid = uuid.UUID(project_id)
    run_uuid = uuid.UUID(run_id)

    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.STAGE_STARTED,
        payload={"stage": "VIDEO", "agent": AGENT_ID},
    )

    try:
        batch = fetch_approved_storyboard_batch(
            settings, project_id=project_uuid, pipeline_run_id=run_uuid
        )
        png_frames = [frame.png_bytes for frame in batch.frames]
        frame_ids = [frame.asset_version_id for frame in batch.frames]

        db_rationale = fetch_latest_video_rejection_rationale(
            settings, pipeline_run_id=run_uuid
        )
        effective_note = (rejection_note or "").strip() or (db_rationale or "")

        source = SOURCE_SLIDESHOW
        fallback_from: str | None = None
        fallback_reason: str | None = None
        mp4_bytes: bytes

        try:
            if getattr(settings, "video_i2v_enabled", False):
                # WAN 2.2 is VRAM-heavy; free the GPU from Ollama first (D-08).
                unload_ollama_before_comfyui(settings)
            candidate = try_comfyui_i2v(settings, png_frames)
            probe = validate_video_mp4(candidate)
            mp4_bytes = candidate
            source = SOURCE_COMFYUI_I2V
        except (VideoI2VError, VideoValidationError, GpuSequencerError) as exc:
            activity.logger.warning(
                "video_i2v_failed",
                extra={"project_id": project_id, "run_id": run_id, "error": str(exc)},
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
            "logical_filename": "scene_video.mp4",
        }
        if effective_note:
            metadata["rejection_note_used"] = effective_note[:500]
        if fallback_from:
            metadata["fallback_from"] = fallback_from
            metadata["fallback_reason"] = fallback_reason

        stored = store_video_asset(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            mp4_bytes=mp4_bytes,
            frame_parent_ids=frame_ids,
            metadata=metadata,
            branch=VIDEO_BRANCH,
        )
    except (
        ApprovedStoryboardNotFoundError,
        AssetStoreError,
        VideoStoreError,
        SlideshowRenderError,
        VideoValidationError,
        RuntimeError,
    ) as exc:
        await _mark_video_failed(project_uuid, run_uuid, exc)
        raise
    except Exception as exc:
        await _mark_video_failed(project_uuid, run_uuid, exc)
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
        },
    )

    activity.logger.info(
        "video_agent_completed",
        extra={
            "project_id": project_id,
            "run_id": run_id,
            "asset_version_id": str(stored.asset_version_id),
            "source": source,
            "video_method": source,
        },
    )
    return str(stored.asset_version_id)


async def _mark_video_failed(
    project_id: uuid.UUID, run_id: uuid.UUID, exc: Exception
) -> None:
    settings = get_settings()
    append_audit_event(
        settings,
        project_id=project_id,
        pipeline_run_id=run_id,
        event_type=AuditEventType.PIPELINE_FAILED,
        payload={"stage": "VIDEO", "error": str(exc), "agent": AGENT_ID},
    )
    await sync_pipeline_status(str(run_id), "FAILED", "VIDEO")
