"""Unit tests for shared pipeline status mapper (US-21 D-59)."""

from __future__ import annotations

import uuid

from aimpos_core.enums import PipelineRunStatus, PipelineStage, ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.pipeline.status_read import build_pipeline_status_read
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository


async def _seed_project(session: AsyncSession) -> Project:
    project = Project(name="Mapper Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()
    return project


async def test_build_pipeline_status_read_idle(session: AsyncSession) -> None:
    project = await _seed_project(session)
    read = build_pipeline_status_read(project.id, None)
    assert read.status == "IDLE"
    assert read.run_id is None
    assert read.stages == ["IDEA", "STORY", "SCRIPT", "STORYBOARD", "VIDEO"]


async def test_build_pipeline_status_read_active_run(session: AsyncSession) -> None:
    project = await _seed_project(session)
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.AWAITING_APPROVAL,
        current_stage=PipelineStage.STORY,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    read = build_pipeline_status_read(project.id, run)
    assert read.status == "AWAITING_APPROVAL"
    assert read.current_stage == "STORY"
    assert read.run_id == run.id
    assert read.updated_at is not None
