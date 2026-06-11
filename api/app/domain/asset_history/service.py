"""Asset history read orchestration (US-22)."""

from __future__ import annotations

import uuid

from aimpos_core.enums import AssetStage
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.asset_history.resolver import build_history_response
from app.domain.asset_history.types import AssetHistoryResponse
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.project import ProjectRepository


class ProjectNotFoundError(Exception):
    """Project does not exist."""


async def get_asset_history(
    project_id: uuid.UUID,
    *,
    session: AsyncSession,
    stage: AssetStage | None = None,
    pipeline_run_id: uuid.UUID | None = None,
) -> AssetHistoryResponse:
    """Read-only asset version history (V-22: no writes)."""
    projects = ProjectRepository(session)
    if await projects.get(project_id) is None:
        raise ProjectNotFoundError(str(project_id))

    assets = AssetVersionRepository(session)
    rows = await assets.list_history_for_project(
        project_id,
        stage=stage,
        pipeline_run_id=pipeline_run_id,
    )
    return build_history_response(project_id, list(rows))
