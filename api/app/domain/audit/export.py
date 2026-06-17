"""Audit trail export serialization (Phase 3B / US-23b export)."""

from __future__ import annotations

import csv
import io
import json
from typing import Literal

from app.domain.audit.types import AuditEventRead

ExportFormat = Literal["json", "csv"]


def serialize_audit_json(events: list[AuditEventRead]) -> bytes:
    payload = [
        {
            "id": str(event.id),
            "project_id": str(event.project_id) if event.project_id else None,
            "pipeline_run_id": str(event.pipeline_run_id) if event.pipeline_run_id else None,
            "event_type": event.event_type,
            "model_id": event.model_id,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


def serialize_audit_csv(events: list[AuditEventRead]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "project_id",
            "pipeline_run_id",
            "event_type",
            "model_id",
            "payload_json",
            "created_at",
        ]
    )
    for event in events:
        writer.writerow(
            [
                str(event.id),
                str(event.project_id) if event.project_id else "",
                str(event.pipeline_run_id) if event.pipeline_run_id else "",
                event.event_type,
                event.model_id or "",
                json.dumps(event.payload, default=str) if event.payload else "",
                event.created_at.isoformat(),
            ]
        )
    return buffer.getvalue().encode("utf-8")
