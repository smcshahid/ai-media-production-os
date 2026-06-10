"""Stub stage activities — no Ollama, ComfyUI, or LangGraph (Sprint 2 boundary)."""

from __future__ import annotations

import logging

from temporalio import activity

logger = logging.getLogger("aimpos.worker.activity")


@activity.defn(name="run_stub_stage")
async def run_stub_stage(stage: str, run_id: str) -> str:
    """Placeholder activity: log stage execution and return a stub artifact id."""
    activity.logger.info("stub_stage_completed", extra={"stage": stage, "run_id": run_id})
    logger.info("stub_stage_completed", extra={"stage": stage, "run_id": run_id})
    return f"stub-{stage.lower()}-{run_id[:8]}"
