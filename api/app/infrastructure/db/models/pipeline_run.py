"""``pipeline_runs`` — workflow instance state (BC: Governed Workflow)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import PipelineRunStatus, PipelineStage
from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, created_at_column, uuid_pk


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    status: Mapped[PipelineRunStatus] = mapped_column(
        Enum(PipelineRunStatus, native_enum=False, length=20),
        nullable=False,
        default=PipelineRunStatus.PENDING,
    )
    current_stage: Mapped[PipelineStage | None] = mapped_column(
        Enum(PipelineStage, native_enum=False, length=16), nullable=True
    )
    # Bound when Temporal lands (US-07, Sprint 2); nullable until then.
    temporal_workflow_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
