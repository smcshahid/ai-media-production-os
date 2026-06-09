"""ProjectRepository + default-project seed tests (T-01-04)."""

from __future__ import annotations

import pytest
from aimpos_core.enums import ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.studio.project import DEFAULT_PROJECT_NAME
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository
from app.seed.default_project import seed_default_project


@pytest.mark.asyncio
async def test_add_get_list_round_trip(session: AsyncSession) -> None:
    repo = ProjectRepository(session)
    project = Project(name="Repo Test", status=ProjectStatus.ACTIVE)
    await repo.add(project)

    fetched = await repo.get(project.id)
    assert fetched is not None
    assert fetched.name == "Repo Test"
    assert [p.id for p in await repo.list()] == [project.id]


@pytest.mark.asyncio
async def test_list_active_excludes_archived(session: AsyncSession) -> None:
    repo = ProjectRepository(session)
    await repo.add(Project(name="Active", status=ProjectStatus.ACTIVE))
    await repo.add(Project(name="Archived", status=ProjectStatus.ARCHIVED))

    active = await repo.list_active()
    assert [p.name for p in active] == ["Active"]


@pytest.mark.asyncio
async def test_seed_creates_one_then_is_idempotent(session: AsyncSession) -> None:
    created = await seed_default_project(session)
    assert created is not None
    assert created.name == DEFAULT_PROJECT_NAME
    assert created.status == ProjectStatus.ACTIVE

    # Second run must not create a duplicate.
    assert await seed_default_project(session) is None

    projects = await ProjectRepository(session).list()
    assert len(projects) == 1
    assert projects[0].name == DEFAULT_PROJECT_NAME
