"""Repository for AuditEvent (append-only log — Sprint 0 plan §4.3)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from aimpos_core.events import AuditEventType
from sqlalchemy import func, select

from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class AuditEventRepository(SQLAlchemyRepository[AuditEvent]):
    model = AuditEvent

    async def append(self, event: AuditEvent) -> AuditEvent:
        """Append-only insert. No update/delete is exposed by domain rule."""

        return await self.add(event)

    async def list_for_run(self, pipeline_run_id: uuid.UUID) -> Sequence[AuditEvent]:
        result = await self.session.execute(
            select(AuditEvent)
            .where(AuditEvent.pipeline_run_id == pipeline_run_id)
            .order_by(AuditEvent.created_at.asc())
        )
        return result.scalars().all()

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        *,
        pipeline_run_id: uuid.UUID | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[AuditEvent]:
        """Project-scoped audit log, optionally filtered to one run (US-23b)."""
        query = select(AuditEvent).where(AuditEvent.project_id == project_id)
        if pipeline_run_id is not None:
            query = query.where(AuditEvent.pipeline_run_id == pipeline_run_id)
        query = query.order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_for_project(
        self,
        project_id: uuid.UUID,
        *,
        pipeline_run_id: uuid.UUID | None = None,
    ) -> int:
        query = select(func.count()).select_from(AuditEvent).where(
            AuditEvent.project_id == project_id
        )
        if pipeline_run_id is not None:
            query = query.where(AuditEvent.pipeline_run_id == pipeline_run_id)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def count_regenerations(self, pipeline_run_id: uuid.UUID, stage: str) -> int:
        events = await self.list_for_run(pipeline_run_id)
        return sum(
            1
            for event in events
            if event.event_type == AuditEventType.REGENERATION_REQUESTED
            and (event.payload or {}).get("stage") == stage
        )
