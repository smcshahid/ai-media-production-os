"""Pipeline stage and run-status enums (ubiquitous language — DDD §4)."""

from enum import StrEnum


class PipelineStage(StrEnum):
    """Stages of the SparkPipelineWorkflow for the Visual MVP.

    Idea -> Story -> Script -> Storyboard. Video/export are deferred per
    MVP Scope Freeze; do not add here without an SCR.
    """

    IDEA = "IDEA"
    STORY = "STORY"
    SCRIPT = "SCRIPT"
    STORYBOARD = "STORYBOARD"


class PipelineRunStatus(StrEnum):
    """Lifecycle state of a ``pipeline_runs`` row."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
