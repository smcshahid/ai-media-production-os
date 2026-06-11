"""Group and sort asset version rows for history (US-22 D-57)."""

from __future__ import annotations

import uuid
from collections import defaultdict

from aimpos_core.enums import AssetStage

from app.domain.asset_history.types import AssetHistoryResponse, AssetHistoryStage, AssetHistoryVersion
from app.infrastructure.db.models.asset_version import AssetVersion

_STAGE_ORDER: tuple[AssetStage, ...] = (
    AssetStage.IDEA,
    AssetStage.STORY,
    AssetStage.SCRIPT,
    AssetStage.STORYBOARD,
    AssetStage.VIDEO,
)


def _version_sort_key(row: AssetVersion) -> tuple[int, int | float]:
    if row.stage == AssetStage.STORYBOARD:
        frame_index = int((row.metadata_json or {}).get("frame_index", 0))
        return (-row.version, frame_index)
    created_ts = row.created_at.timestamp() if row.created_at else 0.0
    return (-row.version, -created_ts)


def _row_to_version(row: AssetVersion) -> AssetHistoryVersion:
    return AssetHistoryVersion(
        asset_id=row.id,
        version=row.version,
        content_hash=row.content_hash,
        is_ai_generated=row.is_ai_generated,
        branch=row.branch,
        pipeline_run_id=row.pipeline_run_id,
        metadata=dict(row.metadata_json or {}),
        created_at=row.created_at,
    )


def build_history_response(
    project_id: uuid.UUID, rows: list[AssetVersion]
) -> AssetHistoryResponse:
    """Build stage-grouped history from flat SELECT rows."""
    by_stage: dict[AssetStage, list[AssetVersion]] = defaultdict(list)
    for row in rows:
        by_stage[row.stage].append(row)

    stages: list[AssetHistoryStage] = []
    for stage in _STAGE_ORDER:
        stage_rows = by_stage.get(stage)
        if not stage_rows:
            continue
        stage_rows.sort(key=_version_sort_key)
        stages.append(
            AssetHistoryStage(
                stage=stage.value,
                versions=[_row_to_version(r) for r in stage_rows],
            )
        )
    return AssetHistoryResponse(project_id=project_id, stages=stages)
