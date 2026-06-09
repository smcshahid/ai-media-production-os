"""Repository for the PipelineRun aggregate root."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class PipelineRunRepository(SQLAlchemyRepository[PipelineRun]):
    model = PipelineRun

    async def list_for_project(self, project_id: uuid.UUID) -> Sequence[PipelineRun]:
        result = await self.session.execute(
            select(PipelineRun)
            .where(PipelineRun.project_id == project_id)
            .order_by(PipelineRun.created_at.desc())
        )
        return result.scalars().all()

    async def latest_for_project(self, project_id: uuid.UUID) -> PipelineRun | None:
        """Return the most recent run for a project, or ``None`` (idle).

        Used by ``GET /pipeline/status`` to render the dashboard stepper.
        """
        result = await self.session.execute(
            select(PipelineRun)
            .where(PipelineRun.project_id == project_id)
            .order_by(PipelineRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
