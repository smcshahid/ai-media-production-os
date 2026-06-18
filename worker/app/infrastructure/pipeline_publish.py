"""Redis publish helper for pipeline status events (US-21 D-59)."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from aimpos_config import get_settings

logger = logging.getLogger("aimpos.worker.pipeline_publish")

_CHANNEL_PREFIX = "aimpos:pipeline:"


def publish_pipeline_status(
    project_id: str,
    run_id: str,
    status: str,
    current_stage: str | None,
    updated_at: datetime | None = None,
    scene_index: int | None = None,
    scene_count: int | None = None,
) -> None:
    """Non-fatal Redis pub/sub publish after DB sync."""
    try:
        import redis

        settings = get_settings()
        client = redis.from_url(settings.redis_url)
        payload: dict[str, Any] = {
            "project_id": project_id,
            "run_id": run_id,
            "status": status,
            "current_stage": current_stage,
        }
        if updated_at is not None:
            payload["updated_at"] = updated_at.isoformat()
        if scene_index is not None:
            payload["current_scene_index"] = scene_index
        if scene_count is not None:
            payload["scene_count"] = scene_count
        client.publish(f"{_CHANNEL_PREFIX}{project_id}", json.dumps(payload))
        client.close()
    except Exception as exc:
        logger.warning(
            "pipeline_status.publish_failed",
            extra={"project_id": project_id, "run_id": run_id, "error": str(exc)},
        )
