"""Lineage read orchestration (US-20)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.lineage.resolver import build_lineage_view
from app.domain.lineage.types import LineageResponse
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.lineage_edge import LineageEdgeRepository
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository


class LineageNotFoundError(Exception):
    """Pipeline run does not exist."""


async def get_lineage_for_run(
    pipeline_run_id: uuid.UUID,
    *,
    session: AsyncSession,
) -> LineageResponse:
    """Read-only lineage for a pipeline run (C-01: no writes)."""
    runs = PipelineRunRepository(session)
    run = await runs.get(pipeline_run_id)
    if run is None:
        raise LineageNotFoundError(str(pipeline_run_id))

    lineage = LineageEdgeRepository(session)
    sql_edges = await lineage.list_edges_for_run(run.project_id, run.id)

    assets = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)
    nodes, edges = await build_lineage_view(
        run,
        assets=assets,
        approvals=approvals,
        sql_edges=sql_edges,
    )

    return LineageResponse(
        pipeline_run_id=run.id,
        project_id=run.project_id,
        nodes=nodes,
        edges=edges,
    )
