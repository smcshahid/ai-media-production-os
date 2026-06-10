"""GET /pipeline/status route tests (idle + latest-run + auth)."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import PipelineRunStatus, PipelineStage, ProjectStatus
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session, get_temporal
from tests.unit.test_pipeline_start import FakeTemporal
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.main import create_app

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


def _transport(session: AsyncSession) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_temporal] = lambda: FakeTemporal()
    return httpx.ASGITransport(app=app)


async def _seed_project(session: AsyncSession) -> Project:
    project = Project(name="Dashboard Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()
    return project


@pytest.mark.asyncio
async def test_status_is_idle_when_no_runs(session: AsyncSession) -> None:
    project = await _seed_project(session)
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/pipeline/status", params={"project_id": str(project.id)}, headers=_AUTH
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "IDLE"
    assert body["run_id"] is None
    assert body["current_stage"] is None
    assert body["stages"] == ["IDEA", "STORY", "SCRIPT", "STORYBOARD"]
    assert body["updated_at"] is None


@pytest.mark.asyncio
async def test_status_reflects_latest_run(session: AsyncSession) -> None:
    project = await _seed_project(session)
    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.RUNNING,
        current_stage=PipelineStage.STORY,
    )
    await PipelineRunRepository(session).add(run)
    await session.commit()
    run_id = str(run.id)

    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/pipeline/status", params={"project_id": str(project.id)}, headers=_AUTH
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RUNNING"
    assert body["current_stage"] == "STORY"
    assert body["run_id"] == run_id
    assert body["updated_at"] is not None


@pytest.mark.asyncio
async def test_unknown_project_returns_404(session: AsyncSession) -> None:
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/pipeline/status", params={"project_id": str(uuid.uuid4())}, headers=_AUTH
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_status_requires_auth(session: AsyncSession) -> None:
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/pipeline/status", params={"project_id": str(uuid.uuid4())})

    assert response.status_code == 401


def test_pipeline_status_registered_in_openapi() -> None:
    schema = create_app().openapi()
    assert "/pipeline/status" in schema["paths"]
    assert "get" in schema["paths"]["/pipeline/status"]
