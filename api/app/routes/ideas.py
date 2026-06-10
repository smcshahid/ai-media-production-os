"""``POST /ideas`` — structured idea capture (US-11 / FEAT-02)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.ideas.service import IdeaValidationError, capture_idea
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.storage.minio_client import MinioClient, StorageError
from app.routes.assets import AssetRead

router = APIRouter(tags=["ideas"])


class IdeaCreateRequest(BaseModel):
    project_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    paragraph: str = Field(min_length=50, max_length=2000)
    style_note: str | None = Field(default=None, max_length=500)


class IdeaCreateResponse(AssetRead):
    """Alias of asset read shape — idea capture returns the new IDEA version."""

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/ideas",
    response_model=IdeaCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Capture a production idea as idea.txt v1+",
)
async def create_idea(
    body: IdeaCreateRequest,
    session: AsyncSession = Depends(get_session),
    minio: MinioClient = Depends(get_minio),
) -> IdeaCreateResponse:
    if await ProjectRepository(session).get(body.project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {body.project_id} not found",
        )

    versions = AssetVersionRepository(session)
    try:
        stored = await capture_idea(
            project_id=body.project_id,
            title=body.title,
            paragraph=body.paragraph,
            style_note=body.style_note,
            blobs=minio,
            versions=versions,
        )
    except IdeaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="asset storage unavailable",
        ) from exc

    await session.commit()
    row = await versions.get(stored.id)
    if row is None:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="idea asset not found after write",
        )
    return IdeaCreateResponse.model_validate(row)
