"""Shared pipeline status read model (US-21 D-59)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import PipelineStage
from pydantic import BaseModel

from app.infrastructure.db.models.pipeline_run import PipelineRun

_IDLE_STATUS = "IDLE"
_STAGE_ORDER = [stage.value for stage in PipelineStage]


class PipelineStatusRead(BaseModel):
    project_id: uuid.UUID
    run_id: uuid.UUID | None
    status: str
    current_stage: str | None
    stages: list[str]
    updated_at: datetime | None


def build_pipeline_status_read(
    project_id: uuid.UUID,
    run: PipelineRun | None,
) -> PipelineStatusRead:
    """Single mapper for REST and WebSocket push (D-59)."""
    if run is None:
        return PipelineStatusRead(
            project_id=project_id,
            run_id=None,
            status=_IDLE_STATUS,
            current_stage=None,
            stages=_STAGE_ORDER,
            updated_at=None,
        )

    return PipelineStatusRead(
        project_id=project_id,
        run_id=run.id,
        status=run.status.value,
        current_stage=run.current_stage.value if run.current_stage else None,
        stages=_STAGE_ORDER,
        updated_at=run.updated_at,
    )
