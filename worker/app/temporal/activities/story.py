"""Story Architect Temporal activity (US-12 / T-12-02)."""

from __future__ import annotations

import uuid

from aimpos_config import get_settings
from aimpos_core.events import AuditEventType
from temporalio import activity

from app.agents.story_architect.constants import AGENT_ID, PROMPT_VERSION, STORY_BRANCH
from app.agents.story_architect.graph import run_story_architect_graph
from app.temporal.activities.pipeline_status import sync_pipeline_status
from app.tools.assets import AssetStoreError, IdeaNotFoundError, fetch_latest_idea, store_story_markdown
from app.tools.audit import append_audit_event


@activity.defn(name="run_story_agent")
async def run_story_agent(project_id: str, run_id: str) -> str:
    """Generate ``story.md`` from the latest IDEA asset and store on ``ai-draft`` branch."""
    settings = get_settings()
    project_uuid = uuid.UUID(project_id)
    run_uuid = uuid.UUID(run_id)

    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.STAGE_STARTED,
        payload={"stage": "STORY", "agent": AGENT_ID},
    )

    try:
        idea = fetch_latest_idea(settings, project_uuid)
        graph_result = run_story_architect_graph(
            settings,
            idea_text=idea.idea_text,
            style_note=idea.style_note,
        )
        stored = store_story_markdown(
            settings,
            project_id=project_uuid,
            pipeline_run_id=run_uuid,
            story_md=graph_result["story_md"],
            branch=STORY_BRANCH,
        )
    except (IdeaNotFoundError, AssetStoreError, RuntimeError) as exc:
        await _mark_story_failed(project_uuid, run_uuid, exc)
        raise
    except Exception as exc:
        await _mark_story_failed(project_uuid, run_uuid, exc)
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
            "branch": STORY_BRANCH,
        },
    )
    append_audit_event(
        settings,
        project_id=project_uuid,
        pipeline_run_id=run_uuid,
        event_type=AuditEventType.ASSET_STORED,
        model_id=model_id,
        payload={
            "stage": "STORY",
            "branch": STORY_BRANCH,
            "content_hash": stored.content_hash,
            "version": stored.version,
        },
    )

    activity.logger.info(
        "story_agent_completed",
        extra={
            "project_id": project_id,
            "run_id": run_id,
            "asset_version_id": str(stored.asset_version_id),
            "model_id": model_id,
        },
    )
    return str(stored.asset_version_id)


async def _mark_story_failed(
    project_id: uuid.UUID, run_id: uuid.UUID, exc: Exception
) -> None:
    settings = get_settings()
    append_audit_event(
        settings,
        project_id=project_id,
        pipeline_run_id=run_id,
        event_type=AuditEventType.PIPELINE_FAILED,
        payload={"stage": "STORY", "error": str(exc), "agent": AGENT_ID},
    )
    await sync_pipeline_status(str(run_id), "FAILED", "STORY")