"""Audit trail routes — read-only event log (US-23b / D-64) + export (Phase 3B)."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.domain.audit.export import serialize_audit_csv, serialize_audit_json
from app.domain.audit.service import ProjectNotFoundError, get_audit_trail
from app.domain.audit.types import AuditTrailResponse

router = APIRouter(tags=["audit"])


@router.get(
    "/audit",
    response_model=AuditTrailResponse,
    summary="Append-only audit trail for a project",
)
async def audit_trail(
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID | None = None,
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> AuditTrailResponse:
    try:
        return await get_audit_trail(
            project_id,
            session=session,
            pipeline_run_id=pipeline_run_id,
            limit=limit,
            offset=offset,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc


@router.get(
    "/audit/export",
    summary="Export audit trail as CSV or JSON",
)
async def audit_trail_export(
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID | None = None,
    format: Literal["csv", "json"] = Query(default="json", alias="format"),
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        trail = await get_audit_trail(
            project_id,
            session=session,
            pipeline_run_id=pipeline_run_id,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc

    scope = pipeline_run_id or "all-runs"
    if format == "csv":
        body = serialize_audit_csv(trail.events)
        media_type = "text/csv"
        filename = f"audit-{project_id}-{scope}.csv"
    else:
        body = serialize_audit_json(trail.events)
        media_type = "application/json"
        filename = f"audit-{project_id}-{scope}.json"

    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
