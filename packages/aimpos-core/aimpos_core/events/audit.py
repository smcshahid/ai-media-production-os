"""Audit event type constants (Repository Structure §4.3 — aimpos-core/events)."""

from enum import StrEnum


class AuditEventType(StrEnum):
    """Types of append-only ``audit_events`` rows.

    AI activities additionally record ``model_id`` for SC-05 traceability
    (see coding-standards.md logging guidance). Workflow- and approval-related
    types are reserved here so the audit schema is stable before Sprint 2.
    """

    PIPELINE_STARTED = "PIPELINE_STARTED"
    STAGE_STARTED = "STAGE_STARTED"
    STAGE_COMPLETED = "STAGE_COMPLETED"
    AGENT_TASK_COMPLETED = "AGENT_TASK_COMPLETED"
    APPROVAL_RECORDED = "APPROVAL_RECORDED"
    ASSET_STORED = "ASSET_STORED"
    PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
    PIPELINE_FAILED = "PIPELINE_FAILED"
