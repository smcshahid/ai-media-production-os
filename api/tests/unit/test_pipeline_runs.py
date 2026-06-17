"""US-31 pipeline run list route tests."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import PipelineRunStatus, PipelineStage, ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.main import create_app

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


def _transport(session: AsyncSession) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return httpx.ASGITransport(app=app)


async def _seed(session: AsyncSession) -> uuid.UUID:
    project = Project(name="Run History", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    runs = PipelineRunRepository(session)
    await runs.add(
        PipelineRun(
            project_id=project.id,
            status=PipelineRunStatus.COMPLETED,
            current_stage=None,
            temporal_workflow_id="spark-pipeline-old",
        )
    )
    await runs.add(
        PipelineRun(
            project_id=project.id,
            status=PipelineRunStatus.AWAITING_APPROVAL,
            current_stage=PipelineStage.VIDEO,
            temporal_workflow_id="spark-pipeline-new",
        )
    )
    await session.commit()
    return project.id


@pytest.mark.asyncio
async def test_pipeline_runs_lists_desc(session: AsyncSession) -> None:
    project_id = await _seed(session)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/pipeline/runs?project_id={project_id}",
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == str(project_id)
    assert len(body["runs"]) == 2
    statuses = {run["status"] for run in body["runs"]}
    assert statuses == {"AWAITING_APPROVAL", "COMPLETED"}


@pytest.mark.asyncio
async def test_pipeline_runs_unknown_project(session: AsyncSession) -> None:
    transport = _transport(session)
    missing = uuid.uuid4()

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/pipeline/runs?project_id={missing}",
            headers=_AUTH,
        )

    assert response.status_code == 404
