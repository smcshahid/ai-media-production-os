"""Character API tests (Phase 7)."""

from __future__ import annotations

import uuid

import pytest
from aimpos_core.character import MAX_CHARACTERS_PER_PROJECT
from aimpos_core.enums import ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.character.service import (
    CharacterLimitError,
    ProjectNotFoundError,
    create_character,
    list_characters,
)
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository


@pytest.mark.asyncio
async def test_create_and_list_characters(session: AsyncSession) -> None:
    project = Project(name="Character pilot", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()

    first = await create_character(
        project_id=project.id,
        name="Maya",
        description="Biologist",
        role="protagonist",
        visual_traits="Short hair",
        personality_notes="Curious",
        session=session,
    )
    await session.commit()

    assert first.character.name == "Maya"
    listed = await list_characters(project.id, session=session)
    assert len(listed.characters) == 1


@pytest.mark.asyncio
async def test_character_limit(session: AsyncSession) -> None:
    project = Project(name="Limit test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()

    for i in range(MAX_CHARACTERS_PER_PROJECT):
        await create_character(
            project_id=project.id,
            name=f"Char {i}",
            description=None,
            role=None,
            visual_traits=None,
            personality_notes=None,
            session=session,
        )
    await session.commit()

    with pytest.raises(CharacterLimitError):
        await create_character(
            project_id=project.id,
            name="One too many",
            description=None,
            role=None,
            visual_traits=None,
            personality_notes=None,
            session=session,
        )


@pytest.mark.asyncio
async def test_list_characters_project_not_found(session: AsyncSession) -> None:
    with pytest.raises(ProjectNotFoundError):
        await list_characters(uuid.uuid4(), session=session)
