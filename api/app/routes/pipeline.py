"""Pipeline routes — status, start (US-07), approve/reject (US-08).

``GET /pipeline/status`` is read-only (D-27). ``POST /pipeline/start`` creates a
``pipeline_runs`` row and starts ``SparkPipelineWorkflow``. ``POST /pipeline/approve``
records immutable ``approvals``, sends Temporal signals, and appends audit events.
Run status is synchronized by worker ``sync_pipeline_status`` (T-07-04).
"""

from __future__ import annotations

import uuid
from typing import Literal

from aimpos_core.character import MAX_CHARACTERS_PER_RUN
from aimpos_core.enums import ApprovalDecision, EpisodeStatus, PipelineRunStatus, PipelineStage
from aimpos_core.events import AuditEventType
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio.service import RPCError

from app.dependencies import get_session, get_temporal
from app.domain.pipeline.run_list import (
    PipelineRunListResponse,
    ProjectNotFoundError as RunListProjectNotFoundError,
    get_pipeline_run_list,
)
from app.domain.pipeline.status_read import PipelineStatusRead, build_pipeline_status_read
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.models.episode import Episode
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.audit_event import AuditEventRepository
from app.domain.character.service import character_snapshot_from_characters
from app.infrastructure.db.repositories.character import CharacterRepository
from app.infrastructure.db.repositories.episode import EpisodeRepository
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.db.repositories.project import ProjectRepository
from app.infrastructure.temporal.client import TemporalService, is_workflow_already_started

_DECIDED_BY = "api-bearer-token"

router = APIRouter(tags=["pipeline"])


class PipelineStartRequest(BaseModel):
    project_id: uuid.UUID
    scene_count: int = Field(default=1, ge=1, le=3)
    episode_id: uuid.UUID | None = None
    character_ids: list[uuid.UUID] | None = Field(default=None, max_length=3)


class PipelineStartResponse(BaseModel):
    project_id: uuid.UUID
    run_id: uuid.UUID
    workflow_id: str
    status: str
    current_stage: str | None
    scene_count: int
    episode_id: uuid.UUID | None = None
    character_ids: list[uuid.UUID] | None = None


class PipelineApproveRequest(BaseModel):
    project_id: uuid.UUID
    episode_id: uuid.UUID | None = None
    stage: PipelineStage
    decision: ApprovalDecision
    note: str | None = Field(default=None, max_length=4000)

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value: object) -> object:
        if isinstance(value, str):
            upper = value.upper()
            if upper == "GRANT":
                return ApprovalDecision.APPROVED
            if upper == "REJECT":
                return ApprovalDecision.REJECTED
        return value


class PipelineApproveResponse(BaseModel):
    project_id: uuid.UUID
    run_id: uuid.UUID
    approval_id: uuid.UUID
    decision: str
    stage: str
    status: str
    current_stage: str | None
    scene_index: int | None = None


@router.get(
    "/pipeline/status",
    response_model=PipelineStatusRead,
    summary="Pipeline status for a project",
)
async def pipeline_status(
    project_id: uuid.UUID,
    episode_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
) -> PipelineStatusRead:
    if await ProjectRepository(session).get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"project {project_id} not found"
        )

    runs = PipelineRunRepository(session)
    episodes = EpisodeRepository(session)
    episode: Episode | None = None
    if episode_id is not None:
        episode = await episodes.get_for_project(project_id, episode_id)
        if episode is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"episode {episode_id} not found for project",
            )
        run = await runs.latest_for_episode(episode_id)
    else:
        run = await runs.latest_for_project(project_id)
        if run and run.episode_id:
            episode = await episodes.get(run.episode_id)

    return build_pipeline_status_read(project_id, run, episode=episode)


@router.get(
    "/pipeline/runs",
    response_model=PipelineRunListResponse,
    summary="Historical pipeline runs for a project (US-31)",
)
async def pipeline_runs(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PipelineRunListResponse:
    try:
        return await get_pipeline_run_list(project_id, session=session)
    except RunListProjectNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project {exc} not found",
        ) from exc


def _temporal_signal_detail(exc: BaseException) -> str:
    """User-facing detail when Temporal workflow is unreachable (Phase 3B UX)."""
    message = str(exc).lower()
    if "not found" in message or "failed" in message or "terminated" in message:
        return (
            "Pipeline workflow is out of sync with the database. "
            "Refresh the dashboard; if the problem persists, contact an operator."
        )
    return "Pipeline workflow signal failed. Try refreshing and retrying."


@router.post(
    "/pipeline/start",
    response_model=PipelineStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start the Spark pipeline workflow for a project",
)
async def pipeline_start(
    body: PipelineStartRequest,
    session: AsyncSession = Depends(get_session),
    temporal: TemporalService = Depends(get_temporal),
) -> PipelineStartResponse:
    project_id = body.project_id
    if await ProjectRepository(session).get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"project {project_id} not found"
        )

    runs = PipelineRunRepository(session)
    episodes = EpisodeRepository(session)
    episode: Episode | None = None
    if body.episode_id is not None:
        episode = await episodes.get_for_project(project_id, body.episode_id)
        if episode is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"episode {body.episode_id} not found for project",
            )
    if await runs.active_for_project(project_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="a pipeline run is already active for this project",
        )

    character_id_strs: list[str] | None = None
    character_snapshot: list[dict[str, str | None]] | None = None
    if body.character_ids:
        if len(body.character_ids) > MAX_CHARACTERS_PER_RUN:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"at most {MAX_CHARACTERS_PER_RUN} characters per run",
            )
        unique_ids = list(dict.fromkeys(body.character_ids))
        chars = await CharacterRepository(session).list_by_ids(project_id, unique_ids)
        if len(chars) != len(unique_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="one or more character_ids not found for project",
            )
        character_id_strs = [str(c.id) for c in chars]
        character_snapshot = character_snapshot_from_characters(list(chars))

    run = PipelineRun(
        project_id=project_id,
        status=PipelineRunStatus.PENDING,
        current_stage=None,
        scene_count=body.scene_count,
        episode_id=body.episode_id,
        character_ids=character_id_strs,
        character_snapshot=character_snapshot,
    )
    await runs.add(run)
    if episode is not None:
        episode.status = EpisodeStatus.IN_PROGRESS
    workflow_id = f"spark-pipeline-{run.id}"
    run.temporal_workflow_id = workflow_id

    try:
        started_id = await temporal.start_spark_pipeline(project_id, run.id)
    except RPCError as exc:
        await session.rollback()
        if is_workflow_already_started(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="workflow already exists for this run",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="temporal workflow start failed",
        ) from exc
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="temporal workflow start failed",
        ) from exc

    run.status = PipelineRunStatus.RUNNING
    run.current_stage = PipelineStage.STORY

    await AuditEventRepository(session).append(
        AuditEvent(
            project_id=project_id,
            pipeline_run_id=run.id,
            event_type=AuditEventType.PIPELINE_STARTED,
            payload={
                "workflow_id": started_id,
                "task_queue": temporal.task_queue,
                "scene_count": body.scene_count,
                "episode_id": str(body.episode_id) if body.episode_id else None,
            },
        )
    )

    await session.commit()

    return PipelineStartResponse(
        project_id=project_id,
        run_id=run.id,
        workflow_id=started_id,
        status=run.status.value,
        current_stage=run.current_stage.value,
        scene_count=body.scene_count,
        episode_id=body.episode_id,
        character_ids=body.character_ids,
    )


def _require_active_run(run: PipelineRun | None) -> PipelineRun:
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no active pipeline run for this project",
        )
    return run


@router.post(
    "/pipeline/approve",
    response_model=PipelineApproveResponse,
    summary="Approve or reject the current stage output",
)
async def pipeline_approve(
    body: PipelineApproveRequest,
    session: AsyncSession = Depends(get_session),
    temporal: TemporalService = Depends(get_temporal),
) -> PipelineApproveResponse:
    project_id = body.project_id
    if await ProjectRepository(session).get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"project {project_id} not found"
        )

    runs = PipelineRunRepository(session)
    if body.episode_id is not None:
        episode = await EpisodeRepository(session).get_for_project(project_id, body.episode_id)
        if episode is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"episode {body.episode_id} not found for project",
            )
        run = _require_active_run(await runs.active_for_episode(body.episode_id))
    else:
        run = _require_active_run(await runs.active_for_project(project_id))

    if run.status != PipelineRunStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"pipeline is not awaiting approval (status={run.status.value})",
        )

    if run.current_stage != body.stage:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"stage mismatch: requested {body.stage.value}, "
                f"current {run.current_stage.value if run.current_stage else None}"
            ),
        )

    if not run.temporal_workflow_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="pipeline run has no bound temporal workflow",
        )

    if body.decision == ApprovalDecision.REJECTED and not (body.note or "").strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="note is required when decision is REJECTED",
        )

    workflow_id = run.temporal_workflow_id
    try:
        if body.decision == ApprovalDecision.APPROVED:
            await temporal.signal_approve(workflow_id, body.stage.value)
        else:
            await temporal.signal_reject(workflow_id, body.stage.value, body.note or "")
    except RPCError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_temporal_signal_detail(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_temporal_signal_detail(exc),
        ) from exc

    approval_scene_index: int | None = None
    if body.stage in (PipelineStage.STORYBOARD, PipelineStage.VIDEO):
        approval_scene_index = run.current_scene_index or 1

    approval = Approval(
        pipeline_run_id=run.id,
        stage=body.stage,
        decision=body.decision,
        rationale=body.note,
        decided_by=_DECIDED_BY,
        scene_index=approval_scene_index,
    )
    await ApprovalRepository(session).add(approval)

    await AuditEventRepository(session).append(
        AuditEvent(
            project_id=project_id,
            pipeline_run_id=run.id,
            event_type=AuditEventType.APPROVAL_RECORDED,
            payload={
                "decision": body.decision.value,
                "stage": body.stage.value,
                "principal": _DECIDED_BY,
                "approval_id": str(approval.id),
                "note": body.note,
                "scene_index": approval_scene_index,
            },
        )
    )

    await session.commit()
    await session.refresh(run)

    return PipelineApproveResponse(
        project_id=project_id,
        run_id=run.id,
        approval_id=approval.id,
        decision=body.decision.value,
        stage=body.stage.value,
        status=run.status.value,
        current_stage=run.current_stage.value if run.current_stage else None,
        scene_index=approval_scene_index,
    )


_SUPPORTED_REGENERATE_STAGES = frozenset(
    {PipelineStage.STORY, PipelineStage.SCRIPT, PipelineStage.STORYBOARD, PipelineStage.VIDEO}
)
_MAX_REGENERATIONS_PER_STAGE = 3


class PipelineRegenerateRequest(BaseModel):
    project_id: uuid.UUID
    stage: PipelineStage


class PipelineRegenerateResponse(BaseModel):
    project_id: uuid.UUID
    run_id: uuid.UUID
    stage: str
    status: str
    current_stage: str | None
    regenerations_used: int


@router.post(
    "/pipeline/regenerate",
    response_model=PipelineRegenerateResponse,
    summary="Regenerate AI output for the current stage after rejection (US-09)",
)
async def pipeline_regenerate(
    body: PipelineRegenerateRequest,
    session: AsyncSession = Depends(get_session),
    temporal: TemporalService = Depends(get_temporal),
) -> PipelineRegenerateResponse:
    project_id = body.project_id
    if await ProjectRepository(session).get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"project {project_id} not found"
        )

    run = _require_active_run(await PipelineRunRepository(session).active_for_project(project_id))

    if run.status != PipelineRunStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"pipeline is not awaiting approval (status={run.status.value})",
        )

    if run.current_stage != body.stage:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"stage mismatch: requested {body.stage.value}, "
                f"current {run.current_stage.value if run.current_stage else None}"
            ),
        )

    if body.stage not in _SUPPORTED_REGENERATE_STAGES:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"regenerate execution not available for stage {body.stage.value}",
        )

    if not run.temporal_workflow_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="pipeline run has no bound temporal workflow",
        )

    approvals = ApprovalRepository(session)
    scene_index = run.current_scene_index if body.stage in (
        PipelineStage.STORYBOARD,
        PipelineStage.VIDEO,
    ) else None
    latest_stage_approval = await approvals.latest_for_stage(
        run.id, body.stage, scene_index=scene_index
    )
    if latest_stage_approval is None or latest_stage_approval.decision != ApprovalDecision.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"stage {body.stage.value} is not in a post-reject state",
        )

    regen_count = await AuditEventRepository(session).count_regenerations(
        run.id, body.stage.value
    )
    if regen_count >= _MAX_REGENERATIONS_PER_STAGE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"regeneration limit reached for stage {body.stage.value} (max {_MAX_REGENERATIONS_PER_STAGE} per run)",
        )

    workflow_id = run.temporal_workflow_id
    try:
        await temporal.signal_regenerate(workflow_id, body.stage.value)
    except RPCError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_temporal_signal_detail(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_temporal_signal_detail(exc),
        ) from exc

    await AuditEventRepository(session).append(
        AuditEvent(
            project_id=project_id,
            pipeline_run_id=run.id,
            event_type=AuditEventType.REGENERATION_REQUESTED,
            payload={
                "stage": body.stage.value,
                "principal": _DECIDED_BY,
                "rejection_approval_id": str(latest_stage_approval.id),
            },
        )
    )

    await session.commit()
    await session.refresh(run)

    return PipelineRegenerateResponse(
        project_id=project_id,
        run_id=run.id,
        stage=body.stage.value,
        status=run.status.value,
        current_stage=run.current_stage.value if run.current_stage else None,
        regenerations_used=regen_count + 1,
    )
