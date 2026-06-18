"""Pipeline run read helpers for worker activities."""

from __future__ import annotations

import uuid

from aimpos_config import Settings
from aimpos_core.scene import DEFAULT_SCENE_INDEX, MAX_SCENES, MIN_SCENES
from sqlalchemy import create_engine, text
from temporalio import activity


def _read_run_scene_count(settings: Settings, *, pipeline_run_id: uuid.UUID) -> int:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT scene_count FROM pipeline_runs
                    WHERE id = :run_id
                    """
                ),
                {"run_id": str(pipeline_run_id)},
            ).first()
    finally:
        engine.dispose()

    if row is None:
        raise RuntimeError(f"pipeline_run {pipeline_run_id} not found")
    count = row[0]
    if count is None:
        return DEFAULT_SCENE_INDEX
    value = int(count)
    if value < MIN_SCENES or value > MAX_SCENES:
        raise RuntimeError(f"invalid scene_count {value} on run {pipeline_run_id}")
    return value


def read_run_episode_number(
    settings: Settings, *, pipeline_run_id: uuid.UUID
) -> int | None:
    """Return episode number for an episode-scoped run, else None (Phase 6)."""
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT e.episode_number
                    FROM pipeline_runs r
                    LEFT JOIN episodes e ON r.episode_id = e.id
                    WHERE r.id = :run_id
                    """
                ),
                {"run_id": str(pipeline_run_id)},
            ).first()
    finally:
        engine.dispose()
    if row is None or row[0] is None:
        return None
    return int(row[0])


@activity.defn(name="fetch_run_scene_count")
async def fetch_run_scene_count(run_id: str) -> int:
    """Return configured scene count for a pipeline run (defaults to 1)."""
    from aimpos_config import get_settings

    settings = get_settings()
    return _read_run_scene_count(settings, pipeline_run_id=uuid.UUID(run_id))
