"""Episode API tests (Phase 6)."""

from __future__ import annotations

import uuid

import pytest
from aimpos_core.enums import ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.episode.service import ProjectNotFoundError, create_episode, list_episodes
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository


@pytest.mark.asyncio
async def test_create_and_list_episodes(session: AsyncSession) -> None:
    project = Project(name="Episode pilot", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()

    first = await create_episode(project_id=project.id, title="Episode One", session=session)
    second = await create_episode(project_id=project.id, title=None, session=session)
    await session.commit()

    assert first.episode.episode_number == 1
    assert second.episode.episode_number == 2

    listed = await list_episodes(project.id, session=session)
    assert len(listed.episodes) == 2
    assert listed.episodes[0].episode_number == 1
    assert listed.episodes[1].episode_number == 2


@pytest.mark.asyncio
async def test_list_episodes_project_not_found(session: AsyncSession) -> None:
    with pytest.raises(ProjectNotFoundError):
        await list_episodes(uuid.uuid4(), session=session)
