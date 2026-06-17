"""Repository for the PipelineRun aggregate root."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from aimpos_core.enums import PipelineRunStatus
from sqlalchemy import select

from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


_ACTIVE_STATUSES = (
    PipelineRunStatus.PENDING,
    PipelineRunStatus.RUNNING,
    PipelineRunStatus.AWAITING_APPROVAL,
)


class PipelineRunRepository(SQLAlchemyRepository[PipelineRun]):
    model = PipelineRun

    async def active_for_project(self, project_id: uuid.UUID) -> PipelineRun | None:
        """Return an in-flight run for ``project_id``, if any (409 guard on start)."""
        result = await self.session.execute(
            select(PipelineRun)
            .where(
                PipelineRun.project_id == project_id,
                PipelineRun.status.in_(_ACTIVE_STATUSES),
            )
            .order_by(PipelineRun.created_at.desc(), PipelineRun.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_for_project(self, project_id: uuid.UUID) -> Sequence[PipelineRun]:
        result = await self.session.execute(
            select(PipelineRun)
            .where(PipelineRun.project_id == project_id)
            .order_by(PipelineRun.created_at.desc(), PipelineRun.id.desc())
        )
        return result.scalars().all()

    async def latest_for_project(self, project_id: uuid.UUID) -> PipelineRun | None:
        """Return the most recent run for a project, or ``None`` (idle).

        Used by ``GET /pipeline/status`` to render the dashboard stepper.
        """
        result = await self.session.execute(
            select(PipelineRun)
            .where(PipelineRun.project_id == project_id)
            .order_by(PipelineRun.created_at.desc(), PipelineRun.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
