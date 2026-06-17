"""US-23b audit trail route tests."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import ProjectStatus
from aimpos_core.events import AuditEventType
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.audit_event import AuditEventRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.main import create_app

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}


def _transport(session: AsyncSession) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return httpx.ASGITransport(app=app)


async def _seed_audit_project(session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    project = Project(name="US-23b Audit", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run_id = uuid.uuid4()
    repo = AuditEventRepository(session)
    await repo.append(
        AuditEvent(
            project_id=project.id,
            pipeline_run_id=run_id,
            event_type=AuditEventType.PIPELINE_STARTED,
            payload={"workflow_id": "spark-pipeline-test"},
        )
    )
    await repo.append(
        AuditEvent(
            project_id=project.id,
            pipeline_run_id=run_id,
            event_type=AuditEventType.STAGE_STARTED,
            payload={"stage": "STORY"},
        )
    )
    await repo.append(
        AuditEvent(
            project_id=project.id,
            pipeline_run_id=uuid.uuid4(),
            event_type=AuditEventType.PIPELINE_STARTED,
            payload={"workflow_id": "other-run"},
        )
    )
    await session.commit()
    return project.id, run_id


@pytest.mark.asyncio
async def test_audit_trail_returns_project_events(session: AsyncSession) -> None:
    project_id, run_id = await _seed_audit_project(session)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/audit?project_id={project_id}", headers=_AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == str(project_id)
    assert len(body["events"]) == 3
    assert body["total"] == 3
    assert body["has_more"] is False
    event_types = {event["event_type"] for event in body["events"]}
    assert "PIPELINE_STARTED" in event_types
    assert "STAGE_STARTED" in event_types


@pytest.mark.asyncio
async def test_audit_trail_filters_by_run(session: AsyncSession) -> None:
    project_id, run_id = await _seed_audit_project(session)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/audit?project_id={project_id}&pipeline_run_id={run_id}",
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["events"]) == 2
    assert all(event["pipeline_run_id"] == str(run_id) for event in body["events"])


@pytest.mark.asyncio
async def test_audit_trail_unknown_project(session: AsyncSession) -> None:
    transport = _transport(session)
    missing = uuid.uuid4()

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/audit?project_id={missing}", headers=_AUTH)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_audit_trail_pagination(session: AsyncSession) -> None:
    project_id, run_id = await _seed_audit_project(session)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        page1 = await client.get(
            f"/audit?project_id={project_id}&limit=2&offset=0",
            headers=_AUTH,
        )
        page2 = await client.get(
            f"/audit?project_id={project_id}&limit=2&offset=2",
            headers=_AUTH,
        )

    assert page1.status_code == 200
    body1 = page1.json()
    assert len(body1["events"]) == 2
    assert body1["total"] == 3
    assert body1["limit"] == 2
    assert body1["offset"] == 0
    assert body1["has_more"] is True

    assert page2.status_code == 200
    body2 = page2.json()
    assert len(body2["events"]) == 1
    assert body2["has_more"] is False
