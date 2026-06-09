"""Repository for the AssetVersion aggregate root."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from aimpos_core.enums import AssetStage
from sqlalchemy import func, select

from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class AssetVersionRepository(SQLAlchemyRepository[AssetVersion]):
    model = AssetVersion

    async def next_version(self, project_id: uuid.UUID, stage: AssetStage) -> int:
        """Return the next version number for a ``(project, stage)`` chain.

        Used by ``store_asset`` (US-05 / T-05-03) to increment versions.
        """

        result = await self.session.execute(
            select(func.max(AssetVersion.version)).where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == stage,
            )
        )
        current = result.scalar_one_or_none()
        return (current or 0) + 1

    async def list_for_project(self, project_id: uuid.UUID) -> Sequence[AssetVersion]:
        result = await self.session.execute(
            select(AssetVersion)
            .where(AssetVersion.project_id == project_id)
            .order_by(AssetVersion.created_at.desc())
        )
        return result.scalars().all()
