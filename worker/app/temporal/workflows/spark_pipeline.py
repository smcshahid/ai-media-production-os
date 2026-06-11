"""SparkPipelineWorkflow — STORY + SCRIPT + STORYBOARD agents + approval gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from aimpos_core.enums import PipelineStage
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.temporal.activities.pipeline_status import sync_pipeline_status
    from app.temporal.activities.script import run_script_agent
    from app.temporal.activities.story import run_story_agent
    from app.temporal.activities.storyboard import run_storyboard_agent

_STAGE_ORDER = (
    PipelineStage.STORY,
    PipelineStage.SCRIPT,
    PipelineStage.STORYBOARD,
)


@dataclass
class SparkPipelineInput:
    project_id: str
    run_id: str


@dataclass
class SparkPipelineWorkflowState:
    current_stage: str | None = None
    awaiting_approval: bool = False
    completed_stages: list[str] = field(default_factory=list)
    last_rejection_note: str | None = None


@workflow.defn(name="SparkPipelineWorkflow")
class SparkPipelineWorkflow:
    """Four-stage Visual MVP pipeline with stub generation and approval signals."""

    def __init__(self) -> None:
        self._state = SparkPipelineWorkflowState()
        self._approval_granted = False
        self._approval_rejected = False
        self._regenerate_requested = False

    @workflow.query
    def get_state(self) -> SparkPipelineWorkflowState:
        return self._state

    @workflow.signal
    def approve(self, stage: str) -> None:
        if self._state.awaiting_approval and (
            self._state.current_stage is None or self._state.current_stage == stage
        ):
            self._approval_granted = True
            self._approval_rejected = False
            self._regenerate_requested = False

    @workflow.signal
    def reject(self, stage: str, note: str = "") -> None:
        if self._state.awaiting_approval and (
            self._state.current_stage is None or self._state.current_stage == stage
        ):
            self._approval_rejected = True
            self._approval_granted = False
            self._regenerate_requested = False
            self._state.last_rejection_note = note or None

    @workflow.signal
    def regenerate(self, stage: str) -> None:
        if self._state.awaiting_approval and (
            self._state.current_stage is None or self._state.current_stage == stage
        ):
            self._regenerate_requested = True
            self._approval_granted = False
            self._approval_rejected = False

    async def _run_stage_generation(
        self, pipeline_input: SparkPipelineInput, stage: PipelineStage
    ) -> None:
        if stage == PipelineStage.STORY:
            rejection_note = self._state.last_rejection_note or ""
            await workflow.execute_activity(
                run_story_agent,
                args=[pipeline_input.project_id, pipeline_input.run_id, rejection_note],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        elif stage == PipelineStage.SCRIPT:
            rejection_note = self._state.last_rejection_note or ""
            await workflow.execute_activity(
                run_script_agent,
                args=[pipeline_input.project_id, pipeline_input.run_id, rejection_note],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        elif stage == PipelineStage.STORYBOARD:
            await workflow.execute_activity(
                run_storyboard_agent,
                args=[pipeline_input.project_id, pipeline_input.run_id],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

    @workflow.run
    async def run(self, pipeline_input: SparkPipelineInput | dict[str, str]) -> str:
        if isinstance(pipeline_input, dict):
            pipeline_input = SparkPipelineInput(**pipeline_input)

        for stage in _STAGE_ORDER:
            self._reset_approval_flags()
            self._state.current_stage = stage.value
            self._state.awaiting_approval = False

            await workflow.execute_activity(
                sync_pipeline_status,
                args=[pipeline_input.run_id, "RUNNING", stage.value],
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            await self._run_stage_generation(pipeline_input, stage)

            await workflow.execute_activity(
                sync_pipeline_status,
                args=[pipeline_input.run_id, "AWAITING_APPROVAL", stage.value],
                start_to_close_timeout=timedelta(seconds=15),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            self._state.awaiting_approval = True
            await workflow.wait_condition(
                lambda: self._approval_granted or self._approval_rejected,
                timeout=timedelta(days=30),
            )

            if self._approval_rejected:
                self._approval_rejected = False
                while not self._approval_granted:
                    await workflow.wait_condition(
                        lambda: self._approval_granted or self._regenerate_requested,
                        timeout=timedelta(days=30),
                    )
                    if self._approval_granted:
                        break

                    self._regenerate_requested = False
                    await workflow.execute_activity(
                        sync_pipeline_status,
                        args=[pipeline_input.run_id, "RUNNING", stage.value],
                        start_to_close_timeout=timedelta(seconds=15),
                        retry_policy=RetryPolicy(maximum_attempts=3),
                    )
                    await self._run_stage_generation(pipeline_input, stage)
                    await workflow.execute_activity(
                        sync_pipeline_status,
                        args=[pipeline_input.run_id, "AWAITING_APPROVAL", stage.value],
                        start_to_close_timeout=timedelta(seconds=15),
                        retry_policy=RetryPolicy(maximum_attempts=3),
                    )

                    await workflow.wait_condition(
                        lambda: self._approval_granted
                        or self._approval_rejected
                        or self._regenerate_requested,
                        timeout=timedelta(days=30),
                    )
                    if self._approval_rejected:
                        self._approval_rejected = False

            self._state.completed_stages.append(stage.value)
            self._state.awaiting_approval = False

        self._state.current_stage = None
        await workflow.execute_activity(
            sync_pipeline_status,
            args=[pipeline_input.run_id, "COMPLETED", None],
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        return "COMPLETED"

    def _reset_approval_flags(self) -> None:
        self._approval_granted = False
        self._approval_rejected = False
        self._regenerate_requested = False
