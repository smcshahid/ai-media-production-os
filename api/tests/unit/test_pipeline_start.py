"""POST /pipeline/start route tests (US-07 / T-07-03, T-07-06)."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import PipelineRunStatus, PipelineStage, ProjectStatus
from aimpos_core.events import AuditEventType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session, get_temporal
from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.main import create_app

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


class FakeTemporal:
    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, uuid.UUID]] = []
        self.approvals: list[tuple[str, str]] = []
        self.rejects: list[tuple[str, str, str]] = []

    async def start_spark_pipeline(self, project_id: uuid.UUID, run_id: uuid.UUID) -> str:
        self.calls.append((project_id, run_id))
        return f"spark-pipeline-{run_id}"

    async def signal_approve(self, workflow_id: str, stage: str) -> None:
        self.approvals.append((workflow_id, stage))

    async def signal_reject(self, workflow_id: str, stage: str, note: str = "") -> None:
        self.rejects.append((workflow_id, stage, note))

    @property
    def task_queue(self) -> str:
        return "aimpos-spark-pipeline"


def _transport(session: AsyncSession, temporal: FakeTemporal | None = None) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    fake = temporal or FakeTemporal()
    app.dependency_overrides[get_temporal] = lambda: fake
    return httpx.ASGITransport(app=app)


async def _seed_project(session: AsyncSession) -> uuid.UUID:
    project = Project(name="Start Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()
    return project.id


@pytest.mark.asyncio
async def test_start_creates_run_workflow_and_audit(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/start",
            json={"project_id": str(project_id)},
            headers=_AUTH,
        )

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == str(project_id)
    assert body["status"] == "RUNNING"
    assert body["current_stage"] == "STORY"
    assert body["workflow_id"] == f"spark-pipeline-{body['run_id']}"
    assert len(fake.calls) == 1

    run = await PipelineRunRepository(session).get(uuid.UUID(body["run_id"]))
    assert run is not None
    assert run.temporal_workflow_id == body["workflow_id"]
    assert run.status == PipelineRunStatus.RUNNING
    assert run.current_stage == PipelineStage.STORY

    result = await session.execute(
        select(AuditEvent).where(AuditEvent.pipeline_run_id == run.id)
    )
    events = result.scalars().all()
    assert len(events) == 1
    assert events[0].event_type == AuditEventType.PIPELINE_STARTED
    assert events[0].payload["workflow_id"] == body["workflow_id"]


@pytest.mark.asyncio
async def test_start_returns_409_when_active_run_exists(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    active = PipelineRun(
        project_id=project_id,
        status=PipelineRunStatus.RUNNING,
        current_stage=PipelineStage.STORY,
    )
    await PipelineRunRepository(session).add(active)
    await session.commit()

    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/start",
            json={"project_id": str(project_id)},
            headers=_AUTH,
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_start_unknown_project_returns_404(session: AsyncSession) -> None:
    transport = _transport(session)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/start",
            json={"project_id": str(uuid.uuid4())},
            headers=_AUTH,
        )

    assert response.status_code == 404
