"""Asset routes — upload, list, content read (US-13), and human-edit save (US-13).

``POST /assets`` + ``GET /assets`` are the US-05 surface. US-13 adds
``GET /assets/{id}/content`` (story text bytes for the Review editor) and
``PUT /assets/{id}`` (human-edit version on branch ``human-edit``). Mutations
use Bearer auth (US-25). Pipeline status is never updated from these routes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from aimpos_core.enums import AssetStage
from aimpos_core.events import AuditEventType
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.assets.service import store_asset
from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.audit_event import AuditEventRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.storage.minio_client import MinioClient, ObjectNotFoundError, StorageError

router = APIRouter(tags=["assets"])

_HUMAN_EDIT_BRANCH = "human-edit"
_MAX_STORY_TEXT_CHARS = 50_000
_STORY_CONTENT_TYPE = "text/markdown; charset=utf-8"


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


class AssetTextUpdateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=_MAX_STORY_TEXT_CHARS)


def _require_story_asset(row: AssetVersion | None, asset_id: uuid.UUID) -> AssetVersion:
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"asset {asset_id} not found",
        )
    if row.stage != AssetStage.STORY:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"content read is limited to STORY assets (got {row.stage.value})",
        )
    return row


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


@router.get(
    "/assets/{asset_id}/content",
    summary="Download STORY asset text (US-13)",
    responses={200: {"content": {_STORY_CONTENT_TYPE: {}}}},
)
async def get_asset_content(
    asset_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    minio: MinioClient = Depends(get_minio),
) -> Response:
    versions = AssetVersionRepository(session)
    row = _require_story_asset(await versions.get(asset_id), asset_id)
    try:
        data = await minio.download_bytes(row.minio_key)
    except ObjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="asset blob not found in storage",
        ) from exc
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="asset storage unavailable",
        ) from exc
    return Response(content=data, media_type=_STORY_CONTENT_TYPE)


@router.put(
    "/assets/{asset_id}",
    response_model=AssetRead,
    summary="Save human-edited STORY text (US-13)",
)
async def update_asset_text(
    asset_id: uuid.UUID,
    body: AssetTextUpdateRequest,
    session: AsyncSession = Depends(get_session),
    minio: MinioClient = Depends(get_minio),
) -> AssetRead:
    versions = AssetVersionRepository(session)
    existing = _require_story_asset(await versions.get(asset_id), asset_id)

    text = body.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="text must not be empty",
        )

    data = text.encode("utf-8")
    try:
        stored = await store_asset(
            data=data,
            stage=AssetStage.STORY,
            project_id=existing.project_id,
            blobs=minio,
            versions=versions,
            content_type="text/markdown",
            is_ai_generated=False,
            branch=_HUMAN_EDIT_BRANCH,
        )
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="asset storage unavailable",
        ) from exc

    await AuditEventRepository(session).append(
        AuditEvent(
            project_id=existing.project_id,
            pipeline_run_id=existing.pipeline_run_id,
            event_type=AuditEventType.ASSET_STORED,
            payload={
                "stage": AssetStage.STORY.value,
                "branch": _HUMAN_EDIT_BRANCH,
                "content_hash": stored.content_hash,
                "asset_version_id": str(stored.id),
                "source_asset_id": str(asset_id),
            },
        )
    )

    await session.commit()
    row = await versions.get(stored.id)
    if row is None:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="asset version not found after write",
        )
    return AssetRead.model_validate(row)
