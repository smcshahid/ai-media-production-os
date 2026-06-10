"""Repository for AuditEvent (append-only log — Sprint 0 plan §4.3)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from aimpos_core.events import AuditEventType
from sqlalchemy import select

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

    async def count_regenerations(self, pipeline_run_id: uuid.UUID, stage: str) -> int:
        events = await self.list_for_run(pipeline_run_id)
        return sum(
            1
            for event in events
            if event.event_type == AuditEventType.REGENERATION_REQUESTED
            and (event.payload or {}).get("stage") == stage
        )
