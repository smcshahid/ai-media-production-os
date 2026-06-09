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
