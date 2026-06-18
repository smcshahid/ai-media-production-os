"""POST /pipeline/approve route tests (US-08 / T-08-01..05)."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import ApprovalDecision, PipelineRunStatus, PipelineStage, ProjectStatus
from aimpos_core.events import AuditEventType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session, get_temporal
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.models.episode import Episode
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from tests.unit.test_pipeline_start import FakeTemporal, _transport

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


async def _seed_project(session: AsyncSession) -> uuid.UUID:
    project = Project(name="Approve Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.commit()
    return project.id


async def _seed_awaiting_run(
    session: AsyncSession,
    project_id: uuid.UUID,
    *,
    stage: PipelineStage = PipelineStage.STORY,
    episode_id: uuid.UUID | None = None,
) -> PipelineRun:
    run = PipelineRun(
        project_id=project_id,
        status=PipelineRunStatus.AWAITING_APPROVAL,
        current_stage=stage,
        temporal_workflow_id=f"spark-pipeline-{uuid.uuid4()}",
        episode_id=episode_id,
    )
    await PipelineRunRepository(session).add(run)
    await session.commit()
    return run


@pytest.mark.asyncio
async def test_approve_records_immutable_row_signal_and_audit(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/approve",
            json={
                "project_id": str(project_id),
                "stage": "STORY",
                "decision": "GRANT",
            },
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "APPROVED"
    assert body["stage"] == "STORY"
    assert len(fake.approvals) == 1
    assert fake.approvals[0] == (run.temporal_workflow_id, "STORY")

    result = await session.execute(select(Approval).where(Approval.pipeline_run_id == run.id))
    approvals = result.scalars().all()
    assert len(approvals) == 1
    assert approvals[0].decision == ApprovalDecision.APPROVED
    assert approvals[0].stage == PipelineStage.STORY

    events = (
        await session.execute(select(AuditEvent).where(AuditEvent.pipeline_run_id == run.id))
    ).scalars().all()
    approval_events = [e for e in events if e.event_type == AuditEventType.APPROVAL_RECORDED]
    assert len(approval_events) == 1
    assert approval_events[0].payload["decision"] == "APPROVED"
    assert approval_events[0].payload["principal"] == "api-bearer-token"


@pytest.mark.asyncio
async def test_reject_sends_signal_stores_note_and_audit(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    run = await _seed_awaiting_run(session, project_id)
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/approve",
            json={
                "project_id": str(project_id),
                "stage": "STORY",
                "decision": "REJECT",
                "note": "needs more detail",
            },
            headers=_AUTH,
        )

    assert response.status_code == 200
    assert len(fake.rejects) == 1
    assert fake.rejects[0][2] == "needs more detail"

    result = await session.execute(select(Approval).where(Approval.pipeline_run_id == run.id))
    row = result.scalars().one()
    assert row.decision == ApprovalDecision.REJECTED
    assert row.rationale == "needs more detail"


@pytest.mark.asyncio
async def test_approve_stage_mismatch_returns_409(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    await _seed_awaiting_run(session, project_id, stage=PipelineStage.STORY)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/approve",
            json={
                "project_id": str(project_id),
                "stage": "SCRIPT",
                "decision": "APPROVED",
            },
            headers=_AUTH,
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_reject_without_note_returns_422(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    await _seed_awaiting_run(session, project_id)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/approve",
            json={
                "project_id": str(project_id),
                "stage": "STORY",
                "decision": "REJECTED",
            },
            headers=_AUTH,
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_approve_with_episode_id_resolves_episode_active_run(session: AsyncSession) -> None:
    project_id = await _seed_project(session)
    episode = Episode(project_id=project_id, episode_number=1, title="Ep1")
    session.add(episode)
    await session.commit()
    await session.refresh(episode)

    legacy_run = await _seed_awaiting_run(session, project_id, stage=PipelineStage.SCRIPT)
    episode_run = await _seed_awaiting_run(
        session, project_id, stage=PipelineStage.STORY, episode_id=episode.id
    )
    fake = FakeTemporal()
    transport = _transport(session, fake)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/pipeline/approve",
            json={
                "project_id": str(project_id),
                "episode_id": str(episode.id),
                "stage": "STORY",
                "decision": "APPROVED",
            },
            headers=_AUTH,
        )

    assert response.status_code == 200
    assert response.json()["run_id"] == str(episode_run.id)
    assert len(fake.approvals) == 1
    assert fake.approvals[0][0] == episode_run.temporal_workflow_id
    assert legacy_run.id != episode_run.id
