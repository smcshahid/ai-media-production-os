"""``audit_events`` — append-only compliance log (BC: Compliance — simplified).

Append-only by domain rule (no UPDATE/DELETE), not by DB constraint in the MVP
(Sprint 0 plan §4.3). ``model_id`` carries the AI model used, for SC-05.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from aimpos_core.events import AuditEventType
from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, created_at_column, uuid_pk


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"), nullable=True, index=True
    )
    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=True, index=True
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, native_enum=False, length=32), nullable=False
    )
    model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = created_at_column()
