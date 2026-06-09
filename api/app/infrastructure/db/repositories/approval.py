"""Repository for the Approval aggregate root (immutable records — DDD AR-03)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class ApprovalRepository(SQLAlchemyRepository[Approval]):
    model = Approval

    async def list_for_run(self, pipeline_run_id: uuid.UUID) -> Sequence[Approval]:
        result = await self.session.execute(
            select(Approval)
            .where(Approval.pipeline_run_id == pipeline_run_id)
            .order_by(Approval.created_at.asc())
        )
        return result.scalars().all()
