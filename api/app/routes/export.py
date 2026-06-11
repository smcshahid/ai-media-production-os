"""Export routes — production bundle download (US-19)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.export.service import (
    ExportNotCompletedError,
    ExportNotFoundError,
    export_pipeline_run,
)
from app.infrastructure.storage.minio_client import MinioClient

router = APIRouter(tags=["export"])


@router.get(
    "/export/{pipeline_run_id}",
    summary="Download production bundle ZIP for a COMPLETED run",
    responses={
        200: {"content": {"application/zip": {}}},
        401: {"description": "Unauthorized"},
        404: {"description": "Run not found"},
        409: {"description": "Run not COMPLETED"},
    },
)
async def download_export(
    pipeline_run_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    minio: MinioClient = Depends(get_minio),
) -> Response:
    try:
        result = await export_pipeline_run(pipeline_run_id, session=session, minio=minio)
    except ExportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"pipeline run {exc.args[0]} not found",
        ) from exc
    except ExportNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"export requires COMPLETED status (current={exc.args[0]})",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    filename = f"aimpos-export-{pipeline_run_id}.zip"
    return Response(
        content=result.zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
