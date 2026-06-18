"""SCRIPT stage Screenwriter activity (US-14 / US-15)."""

from __future__ import annotations

import uuid

from aimpos_config import get_settings
from aimpos_core.events import AuditEventType
from temporalio import activity

from app.agents.screenwriter.constants import AGENT_ID, PROMPT_VERSION, SCRIPT_BRANCH
from app.agents.screenwriter.graph import run_screenwriter_graph
from app.temporal.activities.pipeline_status import sync_pipeline_status
from app.tools.assets import (
    ApprovedStoryNotFoundError,
    AssetStoreError,
    fetch_approved_story,
    fetch_latest_script_rejection_rationale,
    insert_lineage_edge,
    store_script_fountain,
)
from app.tools.audit import append_audit_event
from app.tools.characters import fetch_run_character_profiles
from app.tools.pipeline_run import _read_run_scene_count


@activity.defn(name="run_script_agent")
async def run_script_agent(
    project_id: str, run_id: str, rejection_note: str = ""
) -> str:
    """Generate ``script.fountain`` from approved story (D-37 / D-42)."""
    settings = get_settings()
    project_uuid = uuid.UUID(project_id)
    run_uuid = uuid.UUID(run_id)

    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.STAGE_STARTED,
        payload={"stage": "SCRIPT", "agent": AGENT_ID},
    )

    try:
        # D-42: story input always from approved STORY; never prior SCRIPT drafts.
        story = fetch_approved_story(
            settings, project_id=project_uuid, pipeline_run_id=run_uuid
        )
        db_rationale = fetch_latest_script_rejection_rationale(
            settings, pipeline_run_id=run_uuid
        )
        regen_note = (db_rationale or "").strip()
        if not regen_note and rejection_note.strip():
            regen_note = rejection_note.strip()

        scene_count = _read_run_scene_count(settings, pipeline_run_id=run_uuid)
        _profiles, character_bible = fetch_run_character_profiles(
            settings, pipeline_run_id=run_uuid
        )

        graph_result = run_screenwriter_graph(
            settings,
            story_text=story.story_text,
            rejection_note=regen_note or None,
            scene_count=scene_count,
            character_bible=character_bible or None,
        )
        stored = store_script_fountain(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            script_fountain=graph_result["script_fountain"],
            branch=SCRIPT_BRANCH,
        )
        insert_lineage_edge(
            settings,
            parent_id=story.asset_version_id,
            child_id=stored.asset_version_id,
        )
    except (ApprovedStoryNotFoundError, AssetStoreError, RuntimeError) as exc:
        await _mark_script_failed(project_uuid, run_uuid, exc)
        raise
    except Exception as exc:
        await _mark_script_failed(project_uuid, run_uuid, exc)
        raise

    model_id = graph_result.get("model_id")
    duration_ms = graph_result.get("duration_ms", 0)
    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.AGENT_TASK_COMPLETED,
        model_id=model_id,
        payload={
            "agent": AGENT_ID,
            "asset_version_id": str(stored.asset_version_id),
            "minio_key": stored.minio_key,
            "duration_ms": duration_ms,
            "prompt_version": PROMPT_VERSION,
            "branch": SCRIPT_BRANCH,
        },
    )
    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.ASSET_STORED,
        model_id=model_id,
        payload={
            "stage": "SCRIPT",
            "branch": SCRIPT_BRANCH,
            "content_hash": stored.content_hash,
            "version": stored.version,
        },
    )

    activity.logger.info(
        "script_agent_completed",
        extra={
            "project_id": project_id,
            "run_id": run_id,
            "asset_version_id": str(stored.asset_version_id),
            "model_id": model_id,
        },
    )
    return str(stored.asset_version_id)


async def _mark_script_failed(
    project_id: uuid.UUID, run_id: uuid.UUID, exc: Exception
) -> None:
    settings = get_settings()
    append_audit_event(
        settings,
        project_id=project_id,
        pipeline_run_id=run_id,
        event_type=AuditEventType.PIPELINE_FAILED,
        payload={"stage": "SCRIPT", "error": str(exc), "agent": AGENT_ID},
    )
    await sync_pipeline_status(str(run_id), "FAILED", "SCRIPT")
