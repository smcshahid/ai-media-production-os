"""SparkPipelineWorkflow — STORY through multi-scene STORYBOARD + VIDEO (Phase 4)."""

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
    from app.temporal.activities.video import run_video_agent
    from app.tools.pipeline_run import fetch_run_scene_count

_PRE_SCENE_STAGES = (PipelineStage.STORY, PipelineStage.SCRIPT)
_SCENE_STAGES = (PipelineStage.STORYBOARD, PipelineStage.VIDEO)


@dataclass
class SparkPipelineInput:
    project_id: str
    run_id: str


@dataclass
class SparkPipelineWorkflowState:
    current_stage: str | None = None
    current_scene_index: int | None = None
    scene_count: int | None = None
    awaiting_approval: bool = False
    completed_stages: list[str] = field(default_factory=list)
    last_rejection_note: str | None = None


@workflow.defn(name="SparkPipelineWorkflow")
class SparkPipelineWorkflow:
    """Spark pipeline with human approval gates through final scene VIDEO (D-51/D-78)."""

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
        if self._stage_signal_matches(stage):
            self._approval_granted = True
            self._approval_rejected = False
            self._regenerate_requested = False

    @workflow.signal
    def reject(self, stage: str, note: str = "") -> None:
        if self._stage_signal_matches(stage):
            self._approval_rejected = True
            self._approval_granted = False
            self._regenerate_requested = False
            self._state.last_rejection_note = note or None

    @workflow.signal
    def regenerate(self, stage: str) -> None:
        if self._stage_signal_matches(stage):
            self._regenerate_requested = True
            self._approval_granted = False
            self._approval_rejected = False

    def _stage_signal_matches(self, stage: str) -> bool:
        if not self._state.awaiting_approval:
            return False
        if self._state.current_stage is None:
            return True
        return self._state.current_stage == stage

    async def _run_stage_generation(
        self,
        pipeline_input: SparkPipelineInput,
        stage: PipelineStage,
        *,
        scene_index: int | None = None,
    ) -> None:
        rejection_note = self._state.last_rejection_note or ""
        if stage == PipelineStage.STORY:
            await workflow.execute_activity(
                run_story_agent,
                args=[pipeline_input.project_id, pipeline_input.run_id, rejection_note],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        elif stage == PipelineStage.SCRIPT:
            await workflow.execute_activity(
                run_script_agent,
                args=[pipeline_input.project_id, pipeline_input.run_id, rejection_note],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        elif stage == PipelineStage.STORYBOARD:
            idx = scene_index or 1
            await workflow.execute_activity(
                run_storyboard_agent,
                args=[
                    pipeline_input.project_id,
                    pipeline_input.run_id,
                    rejection_note,
                    idx,
                ],
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
        elif stage == PipelineStage.VIDEO:
            idx = scene_index or 1
            await workflow.execute_activity(
                run_video_agent,
                args=[
                    pipeline_input.project_id,
                    pipeline_input.run_id,
                    rejection_note,
                    idx,
                ],
                start_to_close_timeout=timedelta(minutes=90),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

    async def _sync_status(
        self,
        run_id: str,
        status: str,
        current_stage: str | None,
        *,
        scene_index: int | None = None,
        scene_count: int | None = None,
    ) -> None:
        await workflow.execute_activity(
            sync_pipeline_status,
            args=[run_id, status, current_stage, scene_index, scene_count],
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

    async def _run_stage_with_approval(
        self,
        pipeline_input: SparkPipelineInput,
        stage: PipelineStage,
        *,
        scene_index: int | None = None,
    ) -> None:
        self._reset_approval_flags()
        self._state.current_stage = stage.value
        self._state.current_scene_index = scene_index
        self._state.awaiting_approval = False

        await self._sync_status(
            pipeline_input.run_id,
            "RUNNING",
            stage.value,
            scene_index=scene_index,
            scene_count=self._state.scene_count,
        )

        await self._run_stage_generation(
            pipeline_input, stage, scene_index=scene_index
        )

        await self._sync_status(
            pipeline_input.run_id,
            "AWAITING_APPROVAL",
            stage.value,
            scene_index=scene_index,
            scene_count=self._state.scene_count,
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
                await self._sync_status(
                    pipeline_input.run_id,
                    "RUNNING",
                    stage.value,
                    scene_index=scene_index,
                    scene_count=self._state.scene_count,
                )
                await self._run_stage_generation(
                    pipeline_input, stage, scene_index=scene_index
                )
                await self._sync_status(
                    pipeline_input.run_id,
                    "AWAITING_APPROVAL",
                    stage.value,
                    scene_index=scene_index,
                    scene_count=self._state.scene_count,
                )

                await workflow.wait_condition(
                    lambda: self._approval_granted
                    or self._approval_rejected
                    or self._regenerate_requested,
                    timeout=timedelta(days=30),
                )
                if self._approval_rejected:
                    self._approval_rejected = False

        label = stage.value
        if scene_index is not None:
            label = f"{stage.value}:{scene_index}"
        self._state.completed_stages.append(label)
        self._state.awaiting_approval = False
        self._state.last_rejection_note = None

    @workflow.run
    async def run(self, pipeline_input: SparkPipelineInput | dict[str, str]) -> str:
        if isinstance(pipeline_input, dict):
            pipeline_input = SparkPipelineInput(**pipeline_input)

        for stage in _PRE_SCENE_STAGES:
            await self._run_stage_with_approval(pipeline_input, stage)

        scene_count = await workflow.execute_activity(
            fetch_run_scene_count,
            args=[pipeline_input.run_id],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
        self._state.scene_count = int(scene_count)

        for scene_idx in range(1, self._state.scene_count + 1):
            for stage in _SCENE_STAGES:
                await self._run_stage_with_approval(
                    pipeline_input, stage, scene_index=scene_idx
                )

        self._state.current_stage = None
        self._state.current_scene_index = None
        await self._sync_status(
            pipeline_input.run_id,
            "COMPLETED",
            None,
            scene_index=None,
            scene_count=self._state.scene_count,
        )
        return "COMPLETED"

    def _reset_approval_flags(self) -> None:
        self._approval_granted = False
        self._approval_rejected = False
        self._regenerate_requested = False
