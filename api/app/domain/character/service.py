"""Character read/create/update orchestration (Phase 7 / SCR-2026-005)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.character import MAX_CHARACTERS_PER_PROJECT
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.character import Character
from app.infrastructure.db.repositories.character import CharacterRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    role: str | None
    visual_traits: str | None
    personality_notes: str | None
    created_at: datetime
    updated_at: datetime


class CharacterListResponse(BaseModel):
    project_id: uuid.UUID
    characters: list[CharacterRead]


class CharacterCreateResponse(BaseModel):
    character: CharacterRead


class CharacterUpdateResponse(BaseModel):
    character: CharacterRead


class ProjectNotFoundError(Exception):
    pass


class CharacterNotFoundError(Exception):
    pass


class CharacterLimitError(Exception):
    pass


class CharacterCreateRequest(BaseModel):
    project_id: uuid.UUID
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    role: str | None = Field(default=None, max_length=128)
    visual_traits: str | None = Field(default=None, max_length=4000)
    personality_notes: str | None = Field(default=None, max_length=4000)


class CharacterUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    role: str | None = Field(default=None, max_length=128)
    visual_traits: str | None = Field(default=None, max_length=4000)
    personality_notes: str | None = Field(default=None, max_length=4000)


async def list_characters(
    project_id: uuid.UUID,
    *,
    session: AsyncSession,
) -> CharacterListResponse:
    if await ProjectRepository(session).get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))
    rows = await CharacterRepository(session).list_for_project(project_id)
    return CharacterListResponse(
        project_id=project_id,
        characters=[CharacterRead.model_validate(row) for row in rows],
    )


async def create_character(
    *,
    project_id: uuid.UUID,
    name: str,
    description: str | None,
    role: str | None,
    visual_traits: str | None,
    personality_notes: str | None,
    session: AsyncSession,
) -> CharacterCreateResponse:
    if await ProjectRepository(session).get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))
    repo = CharacterRepository(session)
    if await repo.count_for_project(project_id) >= MAX_CHARACTERS_PER_PROJECT:
        raise CharacterLimitError(
            f"project already has maximum {MAX_CHARACTERS_PER_PROJECT} characters"
        )
    character = Character(
        project_id=project_id,
        name=name.strip(),
        description=description,
        role=role,
        visual_traits=visual_traits,
        personality_notes=personality_notes,
    )
    await repo.add(character)
    await session.flush()
    return CharacterCreateResponse(character=CharacterRead.model_validate(character))


async def update_character(
    *,
    project_id: uuid.UUID,
    character_id: uuid.UUID,
    body: CharacterUpdateRequest,
    session: AsyncSession,
) -> CharacterUpdateResponse:
    if await ProjectRepository(session).get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))
    repo = CharacterRepository(session)
    character = await repo.get_for_project(project_id, character_id)
    if character is None:
        raise CharacterNotFoundError(str(character_id))
    if body.name is not None:
        character.name = body.name.strip()
    if body.description is not None:
        character.description = body.description
    if body.role is not None:
        character.role = body.role
    if body.visual_traits is not None:
        character.visual_traits = body.visual_traits
    if body.personality_notes is not None:
        character.personality_notes = body.personality_notes
    await session.flush()
    return CharacterUpdateResponse(character=CharacterRead.model_validate(character))


def character_profiles_for_export(characters: list[Character]) -> list[dict[str, str | None]]:
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "role": c.role,
            "visual_traits": c.visual_traits,
            "personality_notes": c.personality_notes,
        }
        for c in characters
    ]
