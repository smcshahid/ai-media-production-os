"""Repository for the Approval aggregate root (immutable records — DDD AR-03)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from aimpos_core.enums import ApprovalDecision, PipelineStage
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

    async def latest_for_stage(
        self,
        pipeline_run_id: uuid.UUID,
        stage: PipelineStage,
        *,
        scene_index: int | None = None,
    ) -> Approval | None:
        query = select(Approval).where(
            Approval.pipeline_run_id == pipeline_run_id,
            Approval.stage == stage,
        )
        if scene_index is not None:
            query = query.where(Approval.scene_index == scene_index)
        result = await self.session.execute(
            query.order_by(Approval.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_approved_for_stage(
        self,
        pipeline_run_id: uuid.UUID,
        stage: PipelineStage,
        *,
        scene_index: int | None = None,
    ) -> Approval | None:
        query = select(Approval).where(
            Approval.pipeline_run_id == pipeline_run_id,
            Approval.stage == stage,
            Approval.decision == ApprovalDecision.APPROVED,
        )
        if scene_index is not None:
            query = query.where(Approval.scene_index == scene_index)
        result = await self.session.execute(
            query.order_by(Approval.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_rejected_for_stage(
        self,
        pipeline_run_id: uuid.UUID,
        stage: PipelineStage,
        *,
        scene_index: int | None = None,
    ) -> Approval | None:
        query = select(Approval).where(
            Approval.pipeline_run_id == pipeline_run_id,
            Approval.stage == stage,
            Approval.decision == ApprovalDecision.REJECTED,
        )
        if scene_index is not None:
            query = query.where(Approval.scene_index == scene_index)
        result = await self.session.execute(
            query.order_by(Approval.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
