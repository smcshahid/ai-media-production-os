"""Audit trail read orchestration (US-23b)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.audit.types import AuditEventRead, AuditTrailResponse
from app.infrastructure.db.repositories.audit_event import AuditEventRepository
from app.infrastructure.db.repositories.project import ProjectRepository

DEFAULT_AUDIT_PAGE_SIZE = 100
MAX_AUDIT_PAGE_SIZE = 500


class ProjectNotFoundError(Exception):
    """Project does not exist."""


async def get_audit_trail(
    project_id: uuid.UUID,
    *,
    session: AsyncSession,
    pipeline_run_id: uuid.UUID | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> AuditTrailResponse:
    """Read-only audit event log (append-only source table)."""
    projects = ProjectRepository(session)
    if await projects.get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))

    repo = AuditEventRepository(session)
    total = await repo.count_for_project(project_id, pipeline_run_id=pipeline_run_id)

    page_limit = limit if limit is not None else total
    if limit is not None:
        page_limit = min(max(limit, 1), MAX_AUDIT_PAGE_SIZE)
        offset = max(offset, 0)

    rows = await repo.list_for_project(
        project_id,
        pipeline_run_id=pipeline_run_id,
        limit=page_limit if limit is not None else None,
        offset=offset if limit is not None else 0,
    )
    events = [
        AuditEventRead(
            id=row.id,
            project_id=row.project_id,
            pipeline_run_id=row.pipeline_run_id,
            event_type=row.event_type.value,
            model_id=row.model_id,
            payload=row.payload,
            created_at=row.created_at,
        )
        for row in rows
    ]
    effective_limit = page_limit if limit is not None else total
    effective_offset = offset if limit is not None else 0
    return AuditTrailResponse(
        project_id=project_id,
        pipeline_run_id=pipeline_run_id,
        events=events,
        total=total,
        limit=effective_limit,
        offset=effective_offset,
        has_more=(effective_offset + len(events)) < total,
    )
