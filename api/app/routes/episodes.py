"""Episode REST routes (Phase 6 / SCR-2026-004)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.domain.episode.service import (
    EpisodeCreateRequest,
    EpisodeCreateResponse,
    EpisodeListResponse,
    EpisodeNotFoundError,
    ProjectNotFoundError,
    create_episode,
    list_episodes,
)

router = APIRouter(tags=["episodes"])


@router.get(
    "/episodes",
    response_model=EpisodeListResponse,
    summary="List episodes for a project",
)
async def episodes_list(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> EpisodeListResponse:
    try:
        return await list_episodes(project_id, session=session)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc


@router.post(
    "/episodes",
    response_model=EpisodeCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new episode for a project",
)
async def episodes_create(
    body: EpisodeCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> EpisodeCreateResponse:
    try:
        result = await create_episode(
            project_id=body.project_id,
            title=body.title,
            session=session,
        )
        await session.commit()
        return result
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc
