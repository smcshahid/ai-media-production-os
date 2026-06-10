"""Temporal client adapter — start workflows and send signals (API boundary)."""

from __future__ import annotations

import uuid

from aimpos_config import Settings
from temporalio.client import Client
from temporalio.service import RPCError


class TemporalService:
    """Thin wrapper around the Temporal SDK for pipeline orchestration."""

    def __init__(self, client: Client, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    @property
    def task_queue(self) -> str:
        return self._settings.temporal_task_queue

    async def start_spark_pipeline(self, project_id: uuid.UUID, run_id: uuid.UUID) -> str:
        """Start ``SparkPipelineWorkflow``; return the deterministic workflow id."""
        workflow_id = f"spark-pipeline-{run_id}"
        await self._client.start_workflow(
            "SparkPipelineWorkflow",
            {"project_id": str(project_id), "run_id": str(run_id)},
            id=workflow_id,
            task_queue=self._settings.temporal_task_queue,
        )
        return workflow_id

    async def signal_approve(self, workflow_id: str, stage: str) -> None:
        handle = self._client.get_workflow_handle(workflow_id)
        await handle.signal("approve", stage)

    async def signal_reject(self, workflow_id: str, stage: str, note: str = "") -> None:
        handle = self._client.get_workflow_handle(workflow_id)
        await handle.signal("reject", args=[stage, note])

    async def signal_regenerate(self, workflow_id: str, stage: str) -> None:
        handle = self._client.get_workflow_handle(workflow_id)
        await handle.signal("regenerate", stage)


async def connect_temporal(settings: Settings) -> TemporalService:
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )
    return TemporalService(client, settings)


def is_workflow_already_started(exc: BaseException) -> bool:
    return isinstance(exc, RPCError) and "already started" in str(exc).lower()
