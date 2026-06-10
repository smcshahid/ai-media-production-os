"""Sync ``pipeline_runs`` from workflow activities (T-07-04)."""

from __future__ import annotations

from aimpos_config import get_settings
from sqlalchemy import create_engine, text
from temporalio import activity

_UPDATE = text(
    """
    UPDATE pipeline_runs
    SET status = :status,
        current_stage = :current_stage,
        updated_at = NOW()
    WHERE id = :run_id
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
    with engine.begin() as conn:
        result = conn.execute(
            _UPDATE,
            {"run_id": run_id, "status": status, "current_stage": current_stage},
        )
        if result.rowcount != 1:
            raise RuntimeError(f"pipeline_run {run_id} not found for status sync")
    engine.dispose()
    activity.logger.info(
        "pipeline_status_synced",
        extra={"run_id": run_id, "status": status, "current_stage": current_stage},
    )
