"""T-04-03 acceptance: each repository instantiates and round-trips on a test DB.

Exercises the async SQLAlchemy session pattern end-to-end against an in-memory
database: create -> flush -> read back, for every aggregate-root repository.
"""

from __future__ import annotations

import pytest
from aimpos_core.enums import ApprovalDecision, AssetStage, PipelineStage
from aimpos_core.events import AuditEventType
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    Approval,
    AssetVersion,
    AuditEvent,
    PipelineRun,
    Project,
)
from app.infrastructure.db.repositories import (
    ApprovalRepository,
    AssetVersionRepository,
    AuditEventRepository,
    PipelineRunRepository,
    ProjectRepository,
)


@pytest.mark.asyncio
async def test_project_repository_round_trip(session: AsyncSession) -> None:
    repo = ProjectRepository(session)
    project = await repo.add(Project(name="AIMPOS Spark Demo"))

    fetched = await repo.get(project.id)
    assert fetched is not None
    assert fetched.name == "AIMPOS Spark Demo"
    assert len(await repo.list_active()) == 1


@pytest.mark.asyncio
async def test_pipeline_run_repository_round_trip(session: AsyncSession) -> None:
    project = await ProjectRepository(session).add(Project(name="P"))
    repo = PipelineRunRepository(session)
    run = await repo.add(PipelineRun(project_id=project.id))

    assert await repo.get(run.id) is not None
    assert [r.id for r in await repo.list_for_project(project.id)] == [run.id]


@pytest.mark.asyncio
async def test_asset_version_repository_versions_and_lists(session: AsyncSession) -> None:
    project = await ProjectRepository(session).add(Project(name="P"))
    repo = AssetVersionRepository(session)

    first = await repo.next_version(project.id, AssetStage.IDEA)
    assert first == 1
    await repo.add(
        AssetVersion(
            project_id=project.id,
            stage=AssetStage.IDEA,
            version=first,
            minio_key=f"{project.id}/idea/hash",
            content_hash="hash",
        )
    )
    assert await repo.next_version(project.id, AssetStage.IDEA) == 2
    assert len(await repo.list_for_project(project.id)) == 1


@pytest.mark.asyncio
async def test_approval_repository_round_trip(session: AsyncSession) -> None:
    project = await ProjectRepository(session).add(Project(name="P"))
    run = await PipelineRunRepository(session).add(PipelineRun(project_id=project.id))
    repo = ApprovalRepository(session)

    await repo.add(
        Approval(
            pipeline_run_id=run.id,
            stage=PipelineStage.STORY,
            decision=ApprovalDecision.APPROVED,
        )
    )
    approvals = await repo.list_for_run(run.id)
    assert len(approvals) == 1
    assert approvals[0].decision == ApprovalDecision.APPROVED


@pytest.mark.asyncio
async def test_audit_event_repository_is_append_only(session: AsyncSession) -> None:
    project = await ProjectRepository(session).add(Project(name="P"))
    run = await PipelineRunRepository(session).add(PipelineRun(project_id=project.id))
    repo = AuditEventRepository(session)

    await repo.append(
        AuditEvent(
            project_id=project.id,
            pipeline_run_id=run.id,
            event_type=AuditEventType.PIPELINE_STARTED,
        )
    )
    events = await repo.list_for_run(run.id)
    assert len(events) == 1
    assert events[0].event_type == AuditEventType.PIPELINE_STARTED
