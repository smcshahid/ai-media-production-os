"""Lineage routes — read-only provenance view (US-20)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.domain.lineage.service import LineageNotFoundError, get_lineage_for_run
from app.domain.lineage.types import LineageResponse

router = APIRouter(tags=["lineage"])


@router.get(
    "/lineage/{pipeline_run_id}",
    summary="Read asset lineage for a pipeline run",
    response_model=LineageResponse,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Run not found"},
    },
)
async def read_lineage(
    pipeline_run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> LineageResponse:
    try:
        return await get_lineage_for_run(pipeline_run_id, session=session)
    except LineageNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"pipeline run {exc.args[0]} not found",
        ) from exc
