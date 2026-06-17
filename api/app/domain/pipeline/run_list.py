"""Pipeline run history read model (Phase 3B / US-31)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class PipelineRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    project_id: uuid.UUID
    status: str
    current_stage: str | None
    temporal_workflow_id: str | None
    asset_count: int
    created_at: datetime
    updated_at: datetime


class PipelineRunListResponse(BaseModel):
    project_id: uuid.UUID
    runs: list[PipelineRunSummary]


class ProjectNotFoundError(Exception):
    """Project does not exist."""


async def get_pipeline_run_list(
    project_id: uuid.UUID,
    *,
    session: AsyncSession,
) -> PipelineRunListResponse:
    if await ProjectRepository(session).get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))

    runs = await PipelineRunRepository(session).list_for_project(project_id)
    asset_counts = await _asset_counts_by_run(session, project_id)

    summaries = [
        PipelineRunSummary(
            run_id=run.id,
            project_id=run.project_id,
            status=run.status.value,
            current_stage=run.current_stage.value if run.current_stage else None,
            temporal_workflow_id=run.temporal_workflow_id,
            asset_count=asset_counts.get(run.id, 0),
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
        for run in runs
    ]
    return PipelineRunListResponse(project_id=project_id, runs=summaries)


async def _asset_counts_by_run(
    session: AsyncSession, project_id: uuid.UUID
) -> dict[uuid.UUID, int]:
    result = await session.execute(
        select(AssetVersion.pipeline_run_id, func.count())
        .where(
            AssetVersion.project_id == project_id,
            AssetVersion.pipeline_run_id.is_not(None),
        )
        .group_by(AssetVersion.pipeline_run_id)
    )
    return {row[0]: int(row[1]) for row in result.all() if row[0] is not None}
