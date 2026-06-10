"""US-13 asset content read + human-edit save route tests."""

from __future__ import annotations

import uuid

import httpx
import pytest
from aimpos_config import get_settings
from aimpos_core.enums import AssetStage, PipelineRunStatus, PipelineStage, ProjectStatus
from aimpos_core.events import AuditEventType
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_minio, get_session
from app.domain.assets.service import store_asset
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.audit_event import AuditEventRepository
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.storage.minio_client import ObjectNotFoundError
from app.main import create_app
from app.routes.assets import _HUMAN_EDIT_BRANCH

_AUTH = {"Authorization": f"Bearer {get_settings().api_token}"}
_STORY_MD = b"# Treatment\n\nA lone robot discovers music."


class _FakeBlobStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def upload_bytes(self, key: str, data: bytes, content_type: str) -> str:
        import hashlib

        self.objects[key] = data
        return hashlib.md5(data).hexdigest()

    async def download_bytes(self, key: str) -> bytes:
        if key not in self.objects:
            raise ObjectNotFoundError(f"object not found: {key!r}")
        return self.objects[key]


def _transport(session: AsyncSession, blobs: _FakeBlobStore) -> httpx.ASGITransport:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_minio] = lambda: blobs
    return httpx.ASGITransport(app=app)


async def _seed_story_asset(
    session: AsyncSession, blobs: _FakeBlobStore
) -> tuple[Project, uuid.UUID]:
    project = Project(name="US-13 Test", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    await session.flush()

    run = PipelineRun(
        project_id=project.id,
        status=PipelineRunStatus.AWAITING_APPROVAL,
        current_stage=PipelineStage.STORY,
    )
    await PipelineRunRepository(session).add(run)
    await session.flush()

    versions = AssetVersionRepository(session)
    stored = await store_asset(
        data=_STORY_MD,
        stage=AssetStage.STORY,
        project_id=project.id,
        blobs=blobs,
        versions=versions,
        content_type="text/markdown",
        is_ai_generated=True,
        branch="ai-draft",
    )
    row = await versions.get(stored.id)
    assert row is not None
    row.pipeline_run_id = run.id
    await session.flush()
    await session.commit()
    return project, stored.id


@pytest.mark.asyncio
async def test_get_asset_content_returns_story_bytes(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    _project, asset_id = await _seed_story_asset(session, blobs)
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/{asset_id}/content", headers=_AUTH)

    assert response.status_code == 200
    assert response.text == _STORY_MD.decode("utf-8")
    assert "text/markdown" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_get_asset_content_rejects_non_story_stage(session: AsyncSession) -> None:
    project = Project(name="Idea only", status=ProjectStatus.ACTIVE)
    await ProjectRepository(session).add(project)
    blobs = _FakeBlobStore()
    versions = AssetVersionRepository(session)
    stored = await store_asset(
        data=b"idea",
        stage=AssetStage.IDEA,
        project_id=project.id,
        blobs=blobs,
        versions=versions,
        content_type="text/plain",
    )
    await session.commit()
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/{stored.id}/content", headers=_AUTH)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_asset_content_unknown_id_returns_404(session: AsyncSession) -> None:
    transport = _transport(session, _FakeBlobStore())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/{uuid.uuid4()}/content", headers=_AUTH)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_asset_content_requires_auth(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    _project, asset_id = await _seed_story_asset(session, blobs)
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/assets/{asset_id}/content")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_asset_creates_human_edit_version(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    _project, asset_id = await _seed_story_asset(session, blobs)
    transport = _transport(session, blobs)
    edited = "# Treatment (edited)\n\nHuman revision."

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/assets/{asset_id}",
            json={"text": edited},
            headers=_AUTH,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 2
    assert body["branch"] == _HUMAN_EDIT_BRANCH
    assert body["is_ai_generated"] is False
    assert body["stage"] == "STORY"

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        content_resp = await client.get(f"/assets/{body['id']}/content", headers=_AUTH)
    assert content_resp.text == edited


@pytest.mark.asyncio
async def test_put_asset_does_not_change_pipeline_status(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    project, asset_id = await _seed_story_asset(session, blobs)
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.put(
            f"/assets/{asset_id}",
            json={"text": "Edited story body."},
            headers=_AUTH,
        )
        status_resp = await client.get(
            "/pipeline/status",
            params={"project_id": str(project.id)},
            headers=_AUTH,
        )

    status_body = status_resp.json()
    assert status_body["status"] == PipelineRunStatus.AWAITING_APPROVAL.value
    assert status_body["current_stage"] == PipelineStage.STORY.value


@pytest.mark.asyncio
async def test_put_asset_emits_asset_stored_audit(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    _project, asset_id = await _seed_story_asset(session, blobs)
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        put_resp = await client.put(
            f"/assets/{asset_id}",
            json={"text": "Audit trail check."},
            headers=_AUTH,
        )
    new_id = uuid.UUID(put_resp.json()["id"])

    events = await AuditEventRepository(session).list_for_run(
        (await PipelineRunRepository(session).latest_for_project(_project.id)).id  # type: ignore[union-attr]
    )
    stored_events = [e for e in events if e.event_type == AuditEventType.ASSET_STORED]
    assert len(stored_events) == 1
    assert stored_events[0].payload["branch"] == _HUMAN_EDIT_BRANCH
    assert stored_events[0].payload["asset_version_id"] == str(new_id)


@pytest.mark.asyncio
async def test_put_asset_empty_text_returns_422(session: AsyncSession) -> None:
    blobs = _FakeBlobStore()
    _project, asset_id = await _seed_story_asset(session, blobs)
    transport = _transport(session, blobs)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/assets/{asset_id}",
            json={"text": "   "},
            headers=_AUTH,
        )

    assert response.status_code == 422
