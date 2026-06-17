"""Audit trail read model (US-23b / D-64)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    pipeline_run_id: uuid.UUID | None
    event_type: str
    model_id: str | None
    payload: dict[str, Any] | None
    created_at: datetime


class AuditTrailResponse(BaseModel):
    project_id: uuid.UUID
    pipeline_run_id: uuid.UUID | None
    events: list[AuditEventRead]
    total: int
    limit: int
    offset: int
    has_more: bool
