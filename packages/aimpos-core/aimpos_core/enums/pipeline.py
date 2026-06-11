"""Pipeline stage and run-status enums (ubiquitous language — DDD §4)."""

from enum import StrEnum


class PipelineStage(StrEnum):
    """Stages of the SparkPipelineWorkflow.

    Visual MVP: Idea -> Story -> Script -> Storyboard.
    Spark Full (US-18): adds VIDEO after approved storyboard (D-51).
    """

    IDEA = "IDEA"
    STORY = "STORY"
    SCRIPT = "SCRIPT"
    STORYBOARD = "STORYBOARD"
    VIDEO = "VIDEO"


class PipelineRunStatus(StrEnum):
    """Lifecycle state of a ``pipeline_runs`` row."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
