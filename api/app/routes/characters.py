"""Character REST routes (Phase 7 / SCR-2026-005)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.domain.character.service import (
    CharacterCreateRequest,
    CharacterCreateResponse,
    CharacterLimitError,
    CharacterListResponse,
    CharacterNotFoundError,
    CharacterUpdateRequest,
    CharacterUpdateResponse,
    ProjectNotFoundError,
    create_character,
    list_characters,
    update_character,
)

router = APIRouter(tags=["characters"])


@router.get(
    "/characters",
    response_model=CharacterListResponse,
    summary="List characters for a project",
)
async def characters_list(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> CharacterListResponse:
    try:
        return await list_characters(project_id, session=session)
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc


@router.post(
    "/characters",
    response_model=CharacterCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a character for a project (max 3)",
)
async def characters_create(
    body: CharacterCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> CharacterCreateResponse:
    try:
        result = await create_character(
            project_id=body.project_id,
            name=body.name,
            description=body.description,
            role=body.role,
            visual_traits=body.visual_traits,
            personality_notes=body.personality_notes,
            session=session,
        )
        await session.commit()
        return result
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc
    except CharacterLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.patch(
    "/characters/{character_id}",
    response_model=CharacterUpdateResponse,
    summary="Update a character profile",
)
async def characters_update(
    character_id: uuid.UUID,
    project_id: uuid.UUID,
    body: CharacterUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> CharacterUpdateResponse:
    try:
        result = await update_character(
            project_id=project_id,
            character_id=character_id,
            body=body,
            session=session,
        )
        await session.commit()
        return result
    except ProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc
    except CharacterNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"character {exc} not found",
        ) from exc
