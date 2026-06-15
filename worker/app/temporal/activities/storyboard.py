"""STORYBOARD stage Cinematography + ComfyUI activity (US-16)."""

from __future__ import annotations

import uuid

from aimpos_config import get_settings
from aimpos_core.events import AuditEventType
from temporalio import activity

from app.agents.cinematography.constants import (
    AGENT_ID,
    BASE_SEED,
    PROMPT_VERSION,
    STORYBOARD_BRANCH,
    STORYBOARD_FRAME_COUNT,
    WORKFLOW_NAME,
    apply_quality_suffix,
)
from app.agents.cinematography.graph import run_cinematography_graph
from app.agents.cinematography.validate import validate_shot_plan, validate_storyboard_frame
from app.infrastructure.gpu.sequencer import unload_ollama_before_comfyui
from app.temporal.activities.pipeline_status import sync_pipeline_status
from app.tools.assets import (
    ApprovedScriptNotFoundError,
    AssetStoreError,
    StoryboardBatchStoreError,
    StoryboardFrameInput,
    fetch_approved_script,
    fetch_latest_idea,
    fetch_latest_storyboard_rejection_rationale,
    store_storyboard_batch,
)
from app.tools.audit import append_audit_event
from app.tools.comfyui import ComfyUIError, generate_storyboard_png


@activity.defn(name="run_storyboard_agent")
async def run_storyboard_agent(
    project_id: str, run_id: str, rejection_note: str = ""
) -> str:
    """Generate 4 storyboard PNG frames from approved script (D-41 / D-45)."""
    settings = get_settings()
    project_uuid = uuid.UUID(project_id)
    run_uuid = uuid.UUID(run_id)

    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.STAGE_STARTED,
        payload={"stage": "STORYBOARD", "agent": AGENT_ID},
    )

    try:
        script = fetch_approved_script(
            settings, project_id=project_uuid, pipeline_run_id=run_uuid
        )
        style_note = None
        try:
            idea = fetch_latest_idea(settings, project_uuid)
            style_note = idea.style_note
        except Exception:
            style_note = None

        db_rationale = fetch_latest_storyboard_rejection_rationale(
            settings, pipeline_run_id=run_uuid
        )
        effective_note = (rejection_note or "").strip() or (db_rationale or "")

        graph_result = run_cinematography_graph(
            settings,
            script_fountain=script.script_fountain,
            style_note=style_note,
            rejection_note=effective_note or None,
        )
        shots = graph_result["shots"]
        validate_shot_plan(shots)

        unload_ollama_before_comfyui(settings)

        frame_inputs: list[StoryboardFrameInput] = []
        for shot in sorted(shots, key=lambda s: s["frame_index"]):
            seed = BASE_SEED + int(shot["frame_index"])
            png = generate_storyboard_png(
                settings,
                positive_prompt=apply_quality_suffix(shot["prompt"]),
                seed=seed,
            )
            validate_storyboard_frame(png)
            frame_inputs.append(
                StoryboardFrameInput(
                    frame_index=int(shot["frame_index"]),
                    png_bytes=png,
                    prompt=shot["prompt"],
                    seed=seed,
                    shot_label=shot.get("shot_label") or "Shot",
                )
            )

        if len(frame_inputs) != STORYBOARD_FRAME_COUNT:
            raise RuntimeError(
                f"expected {STORYBOARD_FRAME_COUNT} rendered frames, got {len(frame_inputs)}"
            )

        stored_frames = store_storyboard_batch(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            script_parent_id=script.asset_version_id,
            frames=frame_inputs,
            branch=STORYBOARD_BRANCH,
            workflow_name=WORKFLOW_NAME,
        )
    except (
        ApprovedScriptNotFoundError,
        AssetStoreError,
        StoryboardBatchStoreError,
        ComfyUIError,
        RuntimeError,
    ) as exc:
        await _mark_storyboard_failed(project_uuid, run_uuid, exc)
        raise
    except Exception as exc:
        await _mark_storyboard_failed(project_uuid, run_uuid, exc)
        raise

    model_id = graph_result.get("model_id")
    duration_ms = graph_result.get("duration_ms", 0)
    frame_ids = [str(f.asset_version_id) for f in stored_frames]

    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.AGENT_TASK_COMPLETED,
        model_id=model_id,
        payload={
            "agent": AGENT_ID,
            "frame_count": len(stored_frames),
            "frame_asset_version_ids": frame_ids,
            "duration_ms": duration_ms,
            "prompt_version": PROMPT_VERSION,
            "branch": STORYBOARD_BRANCH,
        },
    )
    for frame in stored_frames:
        append_audit_event(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            event_type=AuditEventType.ASSET_STORED,
            model_id=model_id,
            payload={
                "stage": "STORYBOARD",
                "branch": STORYBOARD_BRANCH,
                "content_hash": frame.content_hash,
                "version": frame.version,
                "frame_index": frame.frame_index,
            },
        )

    activity.logger.info(
        "storyboard_agent_completed",
        extra={
            "project_id": project_id,
            "run_id": run_id,
            "frame_count": len(stored_frames),
            "frame_asset_version_ids": frame_ids,
            "model_id": model_id,
        },
    )
    return ",".join(frame_ids)


async def _mark_storyboard_failed(
    project_id: uuid.UUID, run_id: uuid.UUID, exc: Exception
) -> None:
    settings = get_settings()
    append_audit_event(
        settings,
        project_id=project_id,
        pipeline_run_id=run_id,
        event_type=AuditEventType.PIPELINE_FAILED,
        payload={"stage": "STORYBOARD", "error": str(exc), "agent": AGENT_ID},
    )
    await sync_pipeline_status(str(run_id), "FAILED", "STORYBOARD")
