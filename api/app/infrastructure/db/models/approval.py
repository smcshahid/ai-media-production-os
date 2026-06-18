"""``approvals`` — immutable human approve/reject records (DDD AR-03)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import ApprovalDecision, PipelineStage
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, created_at_column, uuid_pk


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = uuid_pk()
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=False, index=True
    )
    asset_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("asset_versions.id"), nullable=True
    )
    stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage, native_enum=False, length=16), nullable=False
    )
    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(ApprovalDecision, native_enum=False, length=16), nullable=False
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    scene_index: Mapped[int | None] = mapped_column(nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = created_at_column()
