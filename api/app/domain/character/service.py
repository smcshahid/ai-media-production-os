"""Character read/create/update orchestration (Phase 7 / SCR-2026-005)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

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


class CharacterInUseError(Exception):
    """Character bound to an active pipeline run."""
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
    character.updated_at = datetime.now(UTC)
    await session.flush()
    return CharacterUpdateResponse(character=CharacterRead.model_validate(character))


def character_profiles_for_export(characters: list[Character]) -> list[dict[str, str | None]]:
    return [character_profile_dict(c) for c in characters]


def character_profile_dict(character: Character) -> dict[str, str | None]:
    return {
        "id": str(character.id),
        "name": character.name,
        "description": character.description,
        "role": character.role,
        "visual_traits": character.visual_traits,
        "personality_notes": character.personality_notes,
    }


def character_snapshot_from_characters(characters: list[Character]) -> list[dict[str, str | None]]:
    """Immutable profile snapshot stored on pipeline run at start (TD-P7-01)."""
    return character_profiles_for_export(characters)


async def load_characters_for_export(
    run,
    *,
    session: AsyncSession,
) -> list[dict[str, str | None]] | None:
    """Prefer run snapshot; fall back to live rows for legacy runs."""
    if run.character_snapshot:
        return list(run.character_snapshot)
    if not run.character_ids:
        return None
    id_list = [uuid.UUID(str(cid)) for cid in run.character_ids]
    chars = await CharacterRepository(session).list_by_ids(run.project_id, id_list)
    if not chars:
        return None
    return character_profiles_for_export(list(chars))


async def delete_character(
    *,
    project_id: uuid.UUID,
    character_id: uuid.UUID,
    session: AsyncSession,
) -> None:
    if await ProjectRepository(session).get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))
    repo = CharacterRepository(session)
    character = await repo.get_for_project(project_id, character_id)
    if character is None:
        raise CharacterNotFoundError(str(character_id))
    if await repo.is_bound_to_active_run(project_id, character_id):
        raise CharacterInUseError("character is bound to an active pipeline run")
    await repo.delete(character)
    await session.flush()
