"""POST /pipeline/regenerate route tests (US-09)."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import ApprovalDecision, PipelineRunStatus, PipelineStage, ProjectStatus
from aimpos_core.events import AuditEventType
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from tests.unit.test_pipeline_start import FakeTemporal, _transport

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


async def _seed_project(session: AsyncSession) -> uuid.UUID:
    project = Project(name="Regenerate Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()
    return project.id


async def _seed_awaiting_run(
    session: AsyncSession,
    project_id: uuid.UUID,
    *,
    stage: PipelineStage = PipelineStage.STORY,
) -> PipelineRun:
    run = PipelineRun(
        project_id=project_id,
        status=PipelineRunStatus.AWAITING_APPROVAL,
        current_stage=stage,
        temporal_workflow_id=f"spark-pipeline-{uuid.uuid4()}",
    )
    await PipelineRunRepository(session).add(run)
    await session.commit()
    return run


async def _seed_rejected(session: AsyncSession, run: PipelineRun, stage: PipelineStage) -> Approval:
    approval = Approval(
        pipeline_run_id=run.id,
        stage=stage,
        decision=ApprovalDecision.REJECTED,
        rationale="Needs stronger third act.",
        decided_by="test",
    )
    session.add(approval)
    await session.commit()
    return approval


async def _seed_regeneration_audits(
    session: AsyncSession, run: PipelineRun, stage: str, count: int
) -> None:
    for _ in range(count):
        session.add(
            AuditEvent(
                project_id=run.project_id,
                pipeline_run_id=run.id,
                event_type=AuditEventType.REGENERATION_REQUESTED,
                payload={"stage": stage},
            )
        )
    await session.commit()


@pytest.mark.asyncio
async def test_regenerate_happy_path_signal_and_audit(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id)
    await _seed_rejected(session, run, PipelineStage.STORY)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/regenerate",
            json={"project_id": str(project_id), "stage": "STORY"},
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "STORY"
    assert body["regenerations_used"] == 1
    assert len(fake.regenerates) == 1
    assert fake.regenerates[0] == (run.temporal_workflow_id, "STORY")

    audits = (
        await session.execute(
            select(AuditEvent).where(
                AuditEvent.pipeline_run_id == run.id,
                AuditEvent.event_type == AuditEventType.REGENERATION_REQUESTED,
            )
        )
    ).scalars().all()
    assert len(audits) == 1
    assert audits[0].payload["stage"] == "STORY"


@pytest.mark.asyncio
async def test_regenerate_requires_post_reject_state(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/regenerate",
            json={"project_id": str(project_id), "stage": "STORY"},
            headers=_AUTH,
        )

    assert response.status_code == 409
    assert len(fake.regenerates) == 0


@pytest.mark.asyncio
async def test_regenerate_script_stage_happy_path(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id, stage=PipelineStage.SCRIPT)
    await _seed_rejected(session, run, PipelineStage.SCRIPT)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/regenerate",
            json={"project_id": str(project_id), "stage": "SCRIPT"},
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "SCRIPT"
    assert body["regenerations_used"] == 1
    assert len(fake.regenerates) == 1
    assert fake.regenerates[0] == (run.temporal_workflow_id, "SCRIPT")


@pytest.mark.asyncio
async def test_fourth_regenerate_returns_429_without_side_effects(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id)
    await _seed_rejected(session, run, PipelineStage.STORY)
    await _seed_regeneration_audits(session, run, "STORY", 3)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    audit_count_before = (
        await session.execute(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.pipeline_run_id == run.id,
                AuditEvent.event_type == AuditEventType.REGENERATION_REQUESTED,
            )
        )
    ).scalar_one()

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/regenerate",
            json={"project_id": str(project_id), "stage": "STORY"},
            headers=_AUTH,
        )

    assert response.status_code == 429
    assert "limit" in response.json()["detail"].lower()
    assert len(fake.regenerates) == 0

    audit_count_after = (
        await session.execute(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.pipeline_run_id == run.id,
                AuditEvent.event_type == AuditEventType.REGENERATION_REQUESTED,
            )
        )
    ).scalar_one()
    assert audit_count_after == audit_count_before == 3


@pytest.mark.asyncio
async def test_regenerate_storyboard_stage_happy_path(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id, stage=PipelineStage.STORYBOARD)
    await _seed_rejected(session, run, PipelineStage.STORYBOARD)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/regenerate",
            json={"project_id": str(project_id), "stage": "STORYBOARD"},
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "STORYBOARD"
    assert body["regenerations_used"] == 1
    assert len(fake.regenerates) == 1
    assert fake.regenerates[0] == (run.temporal_workflow_id, "STORYBOARD")


@pytest.mark.asyncio
async def test_regenerate_video_stage_happy_path(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id, stage=PipelineStage.VIDEO)
    await _seed_rejected(session, run, PipelineStage.VIDEO)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/regenerate",
            json={"project_id": str(project_id), "stage": "VIDEO"},
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "VIDEO"
    assert body["regenerations_used"] == 1
    assert len(fake.regenerates) == 1
    assert fake.regenerates[0] == (run.temporal_workflow_id, "VIDEO")

