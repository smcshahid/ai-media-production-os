"""Read-only lineage edge queries (US-20 D-55 / C-01).

No write methods — lineage mutation remains worker-only.
"""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.lineage_edge import LineageEdge


class LineageEdgeRepository:
    """Run-scoped SELECT over ``lineage_edges`` (C-01: read-only)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_edges_for_run(
        self, project_id: uuid.UUID, run_id: uuid.UUID
    ) -> list[tuple[uuid.UUID, uuid.UUID]]:
        parent = aliased(AssetVersion)
        child = aliased(AssetVersion)
        result = await self.session.execute(
            select(LineageEdge.parent_id, LineageEdge.child_id)
            .join(parent, LineageEdge.parent_id == parent.id)
            .join(child, LineageEdge.child_id == child.id)
            .where(
                parent.project_id == project_id,
                child.project_id == project_id,
                or_(
                    parent.pipeline_run_id == run_id,
                    child.pipeline_run_id == run_id,
                ),
            )
        )
        return [(row[0], row[1]) for row in result.all()]
