"""``POST /assets`` + ``GET /assets`` — human asset upload & version listing.

The HTTP surface for US-05's asset storage service (Sprint 0 plan §4.6 `POST
/assets`, §4.7 `GET /assets`). These are thin controllers: they wire the MinIO
and repository adapters into the framework-free ``store_asset`` service
(``api/domain/assets``) and own the request-scoped transaction (commit here;
repositories only ``flush``).

Human uploads are always ``is_ai_generated=False`` (plan §4.7); agent outputs
(``True``) are written by the worker via ``store_asset`` directly, not this
endpoint. Auth (Bearer token) arrives with US-25 — like ``GET /projects`` these
are unauthenticated for now.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from aimpos_core.enums import AssetStage
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.assets.service import store_asset
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.storage.minio_client import MinioClient, StorageError

router = APIRouter(tags=["assets"])


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    stage: str
    version: int
    content_hash: str
    minio_key: str
    is_ai_generated: bool
    branch: str
    metadata_json: dict | None = None
    created_at: datetime


@router.post(
    "/assets",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an asset",
)
async def upload_asset(
    project_id: Annotated[uuid.UUID, Form()],
    stage: Annotated[AssetStage, Form()],
    file: Annotated[UploadFile, File()],
    session: AsyncSession = Depends(get_session),
    minio: MinioClient = Depends(get_minio),
) -> AssetRead:
    # Validate the project up front so a bad id returns 404 instead of a blob
    # being written to MinIO ahead of an FK violation on flush.
    if await ProjectRepository(session).get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"project {project_id} not found"
        )

    data = await file.read()
    versions = AssetVersionRepository(session)
    try:
        stored = await store_asset(
            data=data,
            stage=stage,
            project_id=project_id,
            blobs=minio,
            versions=versions,
            content_type=file.content_type or "application/octet-stream",
        )
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="asset storage unavailable"
        ) from exc

    await session.commit()
    row = await versions.get(stored.id)
    if row is None:  # pragma: no cover — the row was just committed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="asset version not found after write",
        )
    return AssetRead.model_validate(row)


@router.get(
    "/assets",
    response_model=list[AssetRead],
    summary="List asset versions for a project",
)
async def list_assets(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[AssetRead]:
    assets = await AssetVersionRepository(session).list_for_project(project_id)
    return [AssetRead.model_validate(asset) for asset in assets]
