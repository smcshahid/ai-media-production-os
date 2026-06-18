"""Repository for the Episode aggregate root (Phase 6)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select

from app.infrastructure.db.models.episode import Episode
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class EpisodeRepository(SQLAlchemyRepository[Episode]):
    model = Episode

    async def list_for_project(self, project_id: uuid.UUID) -> Sequence[Episode]:
        result = await self.session.execute(
            select(Episode)
            .where(Episode.project_id == project_id)
            .order_by(Episode.episode_number.asc(), Episode.id.asc())
        )
        return result.scalars().all()

    async def next_episode_number(self, project_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.max(Episode.episode_number)).where(Episode.project_id == project_id)
        )
        current = result.scalar_one_or_none()
        return int(current or 0) + 1

    async def get(self, episode_id: uuid.UUID) -> Episode | None:
        result = await self.session.execute(
            select(Episode).where(Episode.id == episode_id)
        )
        return result.scalar_one_or_none()

    async def get_for_project(
        self, project_id: uuid.UUID, episode_id: uuid.UUID
    ) -> Episode | None:
        result = await self.session.execute(
            select(Episode).where(
                Episode.id == episode_id,
                Episode.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()
