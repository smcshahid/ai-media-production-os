"""Sync ``pipeline_runs`` from workflow activities (T-07-04 / Phase 4 / Phase 6)."""

from __future__ import annotations

from aimpos_config import get_settings
from sqlalchemy import create_engine, text
from temporalio import activity

from app.infrastructure.pipeline_publish import publish_pipeline_status

_UPDATE = text(
    """
    UPDATE pipeline_runs
    SET status = :status,
        current_stage = :current_stage,
        current_scene_index = :current_scene_index,
        scene_count = COALESCE(:scene_count, scene_count),
        updated_at = NOW()
    WHERE id = :run_id
    RETURNING project_id, updated_at, scene_count, current_scene_index
    """
)

_COMPLETE_EPISODE = text(
    """
    UPDATE episodes
    SET status = 'COMPLETED', updated_at = NOW()
    WHERE id = (
        SELECT episode_id FROM pipeline_runs WHERE id = :run_id AND episode_id IS NOT NULL
    )
    AND :status = 'COMPLETED'
    """
)


@activity.defn(name="sync_pipeline_status")
async def sync_pipeline_status(
    run_id: str,
    status: str,
    current_stage: str | None,
    current_scene_index: int | None = None,
    scene_count: int | None = None,
) -> None:
    """Write run status/stage/scene to PostgreSQL (side effect — not in workflow code)."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    project_id: str | None = None
    updated_at = None
    synced_scene_index: int | None = None
    synced_scene_count: int | None = None
    with engine.begin() as conn:
        result = conn.execute(
            _UPDATE,
            {
                "run_id": run_id,
                "status": status,
                "current_stage": current_stage,
                "current_scene_index": current_scene_index,
                "scene_count": scene_count,
            },
        )
        row = result.fetchone()
        if row is None:
            raise RuntimeError(f"pipeline_run {run_id} not found for status sync")
        project_id = str(row[0])
        updated_at = row[1]
        synced_scene_count = int(row[2]) if row[2] is not None else None
        synced_scene_index = int(row[3]) if row[3] is not None else None
        conn.execute(_COMPLETE_EPISODE, {"run_id": run_id, "status": status})
    engine.dispose()
    if project_id is not None:
        publish_pipeline_status(
            project_id=project_id,
            run_id=run_id,
            status=status,
            current_stage=current_stage,
            updated_at=updated_at,
            scene_index=synced_scene_index,
            scene_count=synced_scene_count,
        )
    activity.logger.info(
        "pipeline_status_synced",
        extra={
            "run_id": run_id,
            "status": status,
            "current_stage": current_stage,
            "current_scene_index": current_scene_index,
            "scene_count": scene_count,
        },
    )
