#!/usr/bin/env python3
"""T-07-01 gate — Temporal health, worker connectivity, task queue, workflow discovery.

Usage (from repo root, worker package installed):
    pip install ./worker
    python scripts/smoke/test_temporal.py

Exit codes:
    0  PASS
    1  FAIL
    2  SKIP — Temporal not reachable
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from app.temporal.activities.pipeline_status import sync_pipeline_status
from app.temporal.activities.stub import run_stub_stage
from app.temporal.workflows.spark_pipeline import SparkPipelineInput, SparkPipelineWorkflow

NAMESPACE = "default"
WORKFLOW_NAME = "SparkPipelineWorkflow"


@activity.defn(name="run_story_agent")
async def run_story_agent_probe(project_id: str, run_id: str) -> str:
    """Hermetic probe — US-12 live path tested separately with Ollama."""
    return f"probe-story-{run_id[:8]}"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def skip(msg: str) -> None:
    print(f"SKIP: {msg}")
    print("SKIP - Temporal gate not run. This is not PASS.")
    raise SystemExit(2)


async def run_gate(host: str, task_queue: str) -> None:
    print(f"Target: {host}  namespace={NAMESPACE}  task_queue={task_queue}\n")

    print("[1/5] Connect Temporal client...")
    try:
        client = await Client.connect(host, namespace=NAMESPACE)
    except Exception as exc:  # noqa: BLE001
        skip(f"cannot connect to Temporal at {host}: {exc}")
    print("  OK - client connected\n")

    print("[2/5] Namespace liveness (list workflows)...")
    async for _ in client.list_workflows():
        break
    print("  OK - workflow service reachable\n")

    print(f"[3/5] Register worker on task queue `{task_queue}`...")
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[SparkPipelineWorkflow],
        activities=[run_story_agent_probe, run_stub_stage, sync_pipeline_status],
    )
    print(
        "  OK - worker configured with SparkPipelineWorkflow + "
        "run_story_agent (probe) + run_stub_stage + sync_pipeline_status\n"
    )

    workflow_id = f"t07-probe-{uuid.uuid4().hex[:8]}"
    run_id = str(uuid.uuid4())
    print(f"[4/5] Start `{WORKFLOW_NAME}` (workflow_id={workflow_id})...")

    async with worker:
        handle = await client.start_workflow(
            SparkPipelineWorkflow.run,
            SparkPipelineInput(project_id=str(uuid.uuid4()), run_id=run_id),
            id=workflow_id,
            task_queue=task_queue,
        )
        state = None
        import time

        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            try:
                state = await handle.query(SparkPipelineWorkflow.get_state)
            except Exception as exc:  # noqa: BLE001
                fail(f"workflow query failed: {exc}")
            if state.current_stage == "STORY" and state.awaiting_approval:
                break
            await asyncio.sleep(0.5)
        if state is None or state.current_stage != "STORY":
            fail(f"expected current_stage STORY after start, got {getattr(state, 'current_stage', None)!r}")
        print(f"  OK - workflow discovered; current_stage={state.current_stage}\n")

        print("[5/5] Task queue poll + activity execution...")
        if not state.awaiting_approval:
            fail("expected awaiting_approval after stage activity (timed out waiting)")
        print(f"  OK - worker executed stage activity on queue `{task_queue}`\n")

        await handle.cancel()

    print("PASS - T-07-01 Temporal gate: health, connectivity, registration, workflow discovery.")


def main() -> int:
    parser = argparse.ArgumentParser(description="T-07-01 Temporal execution gate")
    parser.add_argument("--address", default="127.0.0.1:7233")
    parser.add_argument("--task-queue", default="aimpos-spark-pipeline")
    args = parser.parse_args()
    asyncio.run(run_gate(args.address, args.task_queue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
