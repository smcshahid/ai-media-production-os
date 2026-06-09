"""Project status enum."""

from enum import StrEnum


class ProjectStatus(StrEnum):
    """Status of a project (Sprint 0 plan §4.3)."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
