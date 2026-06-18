"""Episode read/create orchestration (Phase 6 / SCR-2026-004)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import EpisodeStatus
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.episode import Episode
from app.infrastructure.db.repositories.episode import EpisodeRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class EpisodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    episode_number: int
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class EpisodeListResponse(BaseModel):
    project_id: uuid.UUID
    episodes: list[EpisodeRead]


class EpisodeCreateResponse(BaseModel):
    episode: EpisodeRead


class ProjectNotFoundError(Exception):
    """Project does not exist."""


class EpisodeNotFoundError(Exception):
    """Episode does not exist for project."""


async def list_episodes(
    project_id: uuid.UUID,
    *,
    session: AsyncSession,
) -> EpisodeListResponse:
    if await ProjectRepository(session).get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))

    rows = await EpisodeRepository(session).list_for_project(project_id)
    return EpisodeListResponse(
        project_id=project_id,
        episodes=[EpisodeRead.model_validate(row) for row in rows],
    )


async def create_episode(
    *,
    project_id: uuid.UUID,
    title: str | None,
    session: AsyncSession,
) -> EpisodeCreateResponse:
    if await ProjectRepository(session).get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))

    repo = EpisodeRepository(session)
    episode_number = await repo.next_episode_number(project_id)
    episode = Episode(
        project_id=project_id,
        episode_number=episode_number,
        title=title,
        status=EpisodeStatus.DRAFT,
    )
    await repo.add(episode)
    await session.flush()
    return EpisodeCreateResponse(episode=EpisodeRead.model_validate(episode))


class EpisodeCreateRequest(BaseModel):
    project_id: uuid.UUID
    title: str | None = Field(default=None, max_length=255)
