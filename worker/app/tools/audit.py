"""Append-only audit writer for worker activities."""

from __future__ import annotations

import json
import uuid
from typing import Any

from aimpos_config import Settings
from aimpos_core.events import AuditEventType
from sqlalchemy import create_engine, text


def append_audit_event(
    settings: Settings,
    *,
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID,
    event_type: AuditEventType,
    model_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO audit_events (
                        id, project_id, pipeline_run_id, event_type, model_id, payload, created_at
                    ) VALUES (
                        :id, :project_id, :pipeline_run_id, :event_type, :model_id,
                        CAST(:payload AS JSONB), NOW()
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "project_id": str(project_id),
                    "pipeline_run_id": str(pipeline_run_id),
                    "event_type": event_type.value,
                    "model_id": model_id,
                    "payload": json.dumps(payload) if payload is not None else None,
                },
            )
    finally:
        engine.dispose()
