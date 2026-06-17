"""US-23b audit export route tests."""

from __future__ import annotations

import json
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


async def _seed(session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    project = Project(name="Export Audit", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    run_id = uuid.uuid4()
    await AuditEventRepository(session).append(
        AuditEvent(
            project_id=project.id,
            pipeline_run_id=run_id,
            event_type=AuditEventType.STAGE_STARTED,
            payload={"stage": "VIDEO"},
        )
    )
    await session.commit()
    return project.id, run_id


@pytest.mark.asyncio
async def test_audit_export_json(session: AsyncSession) -> None:
    project_id, run_id = await _seed(session)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/audit/export?project_id={project_id}&pipeline_run_id={run_id}&format=json",
            headers=_AUTH,
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = json.loads(response.content)
    assert len(body) == 1
    assert body[0]["event_type"] == "STAGE_STARTED"


@pytest.mark.asyncio
async def test_audit_export_csv(session: AsyncSession) -> None:
    project_id, _ = await _seed(session)
    transport = _transport(session)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/audit/export?project_id={project_id}&format=csv",
            headers=_AUTH,
        )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    text = response.content.decode("utf-8")
    assert text.startswith("id,project_id,pipeline_run_id")
    assert "STAGE_STARTED" in text
