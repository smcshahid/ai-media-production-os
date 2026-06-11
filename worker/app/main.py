"""Temporal worker entrypoint — registers SparkPipelineWorkflow (US-07 / T-07-05)."""

from __future__ import annotations

import asyncio
import logging
import signal

from aimpos_config import configure_logging, get_settings
from temporalio.client import Client
from temporalio.worker import Worker

from app.temporal.activities.pipeline_status import sync_pipeline_status
from app.temporal.activities.script import run_script_agent
from app.temporal.activities.story import run_story_agent
from app.temporal.activities.storyboard import run_storyboard_agent
from app.temporal.activities.stub import run_stub_stage
from app.temporal.workflows.spark_pipeline import SparkPipelineWorkflow

configure_logging()
logger = logging.getLogger("aimpos.worker")


async def run_worker() -> None:
    settings = get_settings()
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[SparkPipelineWorkflow],
        activities=[
            run_stub_stage,
            run_story_agent,
            run_script_agent,
            run_storyboard_agent,
            sync_pipeline_status,
        ],
    )
    logger.info(
        "worker.registered",
        extra={
            "temporal_address": settings.temporal_address,
            "namespace": settings.temporal_namespace,
            "task_queue": settings.temporal_task_queue,
            "workflows": ["SparkPipelineWorkflow"],
            "activities": [
                "run_stub_stage",
                "run_story_agent",
                "run_script_agent",
                "run_storyboard_agent",
                "sync_pipeline_status",
            ],
        },
    )
    await worker.run()


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    task = loop.create_task(run_worker())

    def _shutdown() -> None:
        task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            # Windows does not support add_signal_handler in the default loop.
            pass

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        logger.info("worker.shutdown")


if __name__ == "__main__":
    main()
