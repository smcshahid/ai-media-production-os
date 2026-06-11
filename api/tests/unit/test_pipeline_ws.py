"""WebSocket /ws/pipeline protocol tests (US-21 D-59)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from aimpos_config import get_settings
from aimpos_core.enums import PipelineRunStatus, PipelineStage, ProjectStatus
from starlette.testclient import TestClient

from app.infrastructure.db.models import Base
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.db.session import build_engine, build_sessionmaker
from app.main import create_app

_TOKEN = get_settings().api_token


@pytest_asyncio.fixture
async def ws_client() -> AsyncIterator[tuple[TestClient, object]]:
    engine = build_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = build_sessionmaker(engine)
    app = create_app()
    with TestClient(app) as client:
        client.app.state.sessionmaker = sessionmaker
        client.app.state.engine = engine
        yield client, sessionmaker
    await engine.dispose()


async def _seed_running_project(sessionmaker) -> Project:
    async with sessionmaker() as session:
        project = Project(name="WS Test", status=ProjectStatus.ACTIVE)
        await ProjectRepository(session).add(project)
        run = PipelineRun(
            project_id=project.id,
            status=PipelineRunStatus.RUNNING,
            current_stage=PipelineStage.STORY,
        )
        session.add(run)
        await session.commit()
        await session.refresh(project)
        return project


@pytest.mark.asyncio
async def test_ws_auth_subscribe_and_snapshot(ws_client) -> None:
    client, sessionmaker = ws_client
    project = await _seed_running_project(sessionmaker)

    with client.websocket_connect("/ws/pipeline") as ws:
        ws.send_json({"type": "auth", "token": _TOKEN})
        assert ws.receive_json() == {"type": "auth.ok"}
        ws.send_json({"type": "subscribe", "project_id": str(project.id)})
        subscribed = ws.receive_json()
        assert subscribed["type"] == "subscribed"
        assert subscribed["project_id"] == str(project.id)
        event = ws.receive_json()
        assert event["type"] == "pipeline.status"
        assert event["payload"]["status"] == "RUNNING"
        assert event["payload"]["current_stage"] == "STORY"


@pytest.mark.asyncio
async def test_ws_rejects_missing_auth(ws_client) -> None:
    client, _sessionmaker = ws_client

    with pytest.raises(Exception):
        with client.websocket_connect("/ws/pipeline") as ws:
            ws.send_json({"type": "subscribe", "project_id": str(uuid.uuid4())})
            ws.receive_json()


@pytest.mark.asyncio
async def test_ws_payload_matches_rest(ws_client) -> None:
    client, sessionmaker = ws_client
    project = await _seed_running_project(sessionmaker)

    rest = client.get(
        "/pipeline/status",
        params={"project_id": str(project.id)},
        headers={"Authorization": f"Bearer {_TOKEN}"},
    )
    assert rest.status_code == 200

    with client.websocket_connect("/ws/pipeline") as ws:
        ws.send_json({"type": "auth", "token": _TOKEN})
        ws.receive_json()
        ws.send_json({"type": "subscribe", "project_id": str(project.id)})
        ws.receive_json()
        event = ws.receive_json()

    assert event["payload"] == rest.json()
