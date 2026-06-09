"""``GET /pipeline/status`` — pipeline state for a project's dashboard.

Sprint 0 plan §4.6 (Basic Backend) / §4.7 (frontend Dashboard stepper). This is
**read-only**: Sprint 0 must not start or approve pipelines (those are Sprint 1+).
With no runs yet the endpoint reports ``IDLE`` plus the canonical 4-stage order so
the dashboard can render the idle stepper; once US-07 starts runs it reflects the
latest run's status and current stage. ``IDLE`` is a presentation sentinel — it is
not a ``PipelineRunStatus`` value (those describe an actual run).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import PipelineStage
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository

router = APIRouter(tags=["pipeline"])

_IDLE_STATUS = "IDLE"
_STAGE_ORDER = [stage.value for stage in PipelineStage]


class PipelineStatusRead(BaseModel):
    project_id: uuid.UUID
    run_id: uuid.UUID | None
    status: str
    current_stage: str | None
    stages: list[str]
    updated_at: datetime | None


@router.get(
    "/pipeline/status",
    response_model=PipelineStatusRead,
    summary="Pipeline status for a project",
)
async def pipeline_status(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PipelineStatusRead:
    if await ProjectRepository(session).get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"project {project_id} not found"
        )

    run = await PipelineRunRepository(session).latest_for_project(project_id)
    if run is None:
        return PipelineStatusRead(
            project_id=project_id,
            run_id=None,
            status=_IDLE_STATUS,
            current_stage=None,
            stages=_STAGE_ORDER,
            updated_at=None,
        )

    return PipelineStatusRead(
        project_id=project_id,
        run_id=run.id,
        status=run.status.value,
        current_stage=run.current_stage.value if run.current_stage else None,
        stages=_STAGE_ORDER,
        updated_at=run.updated_at,
    )
