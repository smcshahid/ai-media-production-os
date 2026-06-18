"""Character snapshot export tests (Phase 7.5 / TD-P7-01)."""

from __future__ import annotations

import pytest
from aimpos_core.enums import PipelineRunStatus, ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.character.service import (
    CharacterInUseError,
    create_character,
    delete_character,
    load_characters_for_export,
)
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository


@pytest.mark.asyncio
async def test_export_uses_snapshot_after_character_deleted(session: AsyncSession) -> None:
    project = Project(name="Snapshot export", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()

    created = await create_character(
        project_id=project.id,
        name="Maya",
        description="Biologist",
        role="protagonist",
        visual_traits="Lab coat",
        personality_notes="Curious",
        session=session,
    )
    await session.commit()
    snapshot = [
        {
            "id": str(created.character.id),
            "name": "Maya",
            "description": "Biologist",
            "role": "protagonist",
            "visual_traits": "Lab coat",
            "personality_notes": "Curious",
        }
    ]
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.COMPLETED,
        character_ids=[str(created.character.id)],
        character_snapshot=snapshot,
    )
    session.add(run)
    await session.flush()

    payload = await load_characters_for_export(run, session=session)
    assert payload == snapshot

    await delete_character(
        project_id=project.id,
        character_id=created.character.id,
        session=session,
    )
    await session.commit()

    payload_after = await load_characters_for_export(run, session=session)
    assert payload_after == snapshot


@pytest.mark.asyncio
async def test_delete_blocked_when_character_in_active_run(session: AsyncSession) -> None:
    project = Project(name="Active run block", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    created = await create_character(
        project_id=project.id,
        name="Eli",
        description=None,
        role="mentor",
        visual_traits=None,
        personality_notes=None,
        session=session,
    )
    await session.flush()
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.RUNNING,
        character_ids=[str(created.character.id)],
        character_snapshot=[
            {
                "id": str(created.character.id),
                "name": "Eli",
                "description": None,
                "role": "mentor",
                "visual_traits": None,
                "personality_notes": None,
            }
        ],
    )
    session.add(run)
    await session.flush()

    with pytest.raises(CharacterInUseError):
        await delete_character(
            project_id=project.id,
            character_id=created.character.id,
            session=session,
        )
