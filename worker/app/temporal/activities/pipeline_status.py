"""Sync ``pipeline_runs`` from workflow activities (T-07-04)."""

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
        updated_at = NOW()
    WHERE id = :run_id
    RETURNING project_id, updated_at
    """
)


@activity.defn(name="sync_pipeline_status")
async def sync_pipeline_status(
    run_id: str,
    status: str,
    current_stage: str | None,
) -> None:
    """Write run status/stage to PostgreSQL (side effect — not in workflow code)."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    project_id: str | None = None
    updated_at = None
    with engine.begin() as conn:
        result = conn.execute(
            _UPDATE,
            {"run_id": run_id, "status": status, "current_stage": current_stage},
        )
        row = result.fetchone()
        if row is None:
            raise RuntimeError(f"pipeline_run {run_id} not found for status sync")
        project_id = str(row[0])
        updated_at = row[1]
    engine.dispose()
    if project_id is not None:
        publish_pipeline_status(
            project_id=project_id,
            run_id=run_id,
            status=status,
            current_stage=current_stage,
            updated_at=updated_at,
        )
    activity.logger.info(
        "pipeline_status_synced",
        extra={"run_id": run_id, "status": status, "current_stage": current_stage},
    )
