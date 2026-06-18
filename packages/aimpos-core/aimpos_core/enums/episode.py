"""Episode status enum — Phase 6 episode model pilot (SCR-2026-004)."""

from enum import StrEnum


class EpisodeStatus(StrEnum):
    """Lifecycle status for an episode within a project."""

    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
