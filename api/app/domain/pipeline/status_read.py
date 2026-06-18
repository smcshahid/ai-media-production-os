"""Shared pipeline status read model (US-21 D-59 / Phase 4 multi-scene / Phase 6 episode)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import PipelineStage
from pydantic import BaseModel

from app.infrastructure.db.models.episode import Episode
from app.infrastructure.db.models.pipeline_run import PipelineRun

_IDLE_STATUS = "IDLE"
_STAGE_ORDER = [stage.value for stage in PipelineStage]


class PipelineStatusRead(BaseModel):
    project_id: uuid.UUID
    run_id: uuid.UUID | None
    status: str
    current_stage: str | None
    current_scene_index: int | None = None
    scene_count: int | None = None
    episode_id: uuid.UUID | None = None
    episode_number: int | None = None
    episode_title: str | None = None
    stages: list[str]
    updated_at: datetime | None


def build_pipeline_status_read(
    project_id: uuid.UUID,
    run: PipelineRun | None,
    *,
    episode: Episode | None = None,
) -> PipelineStatusRead:
    """Single mapper for REST and WebSocket push (D-59 / D-77 / D-87)."""
    if run is None:
        ep_id = episode.id if episode else None
        ep_num = episode.episode_number if episode else None
        ep_title = episode.title if episode else None
        return PipelineStatusRead(
            project_id=project_id,
            run_id=None,
            status=_IDLE_STATUS,
            current_stage=None,
            current_scene_index=None,
            scene_count=None,
            episode_id=ep_id,
            episode_number=ep_num,
            episode_title=ep_title,
            stages=_STAGE_ORDER,
            updated_at=None,
        )

    ep_id: uuid.UUID | None = None
    ep_num: int | None = None
    ep_title: str | None = None
    if episode is not None:
        ep_id = episode.id
        ep_num = episode.episode_number
        ep_title = episode.title
    elif run.episode_id is not None:
        ep_id = run.episode_id

    return PipelineStatusRead(
        project_id=project_id,
        run_id=run.id,
        status=run.status.value,
        current_stage=run.current_stage.value if run.current_stage else None,
        current_scene_index=run.current_scene_index,
        scene_count=run.scene_count,
        episode_id=ep_id,
        episode_number=ep_num,
        episode_title=ep_title,
        stages=_STAGE_ORDER,
        updated_at=run.updated_at,
    )
