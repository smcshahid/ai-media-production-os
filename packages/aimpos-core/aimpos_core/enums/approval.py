"""Approval decision enum (immutable approve/reject — DDD AR-03)."""

from enum import StrEnum


class ApprovalDecision(StrEnum):
    """An immutable human approval decision recorded against a stage output."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
