"""Repository for the Project aggregate root."""

from __future__ import annotations

from collections.abc import Sequence

from aimpos_core.enums import ProjectStatus
from sqlalchemy import select

from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class ProjectRepository(SQLAlchemyRepository[Project]):
    model = Project

    async def list_active(self) -> Sequence[Project]:
        result = await self.session.execute(
            select(Project).where(Project.status == ProjectStatus.ACTIVE)
        )
        return result.scalars().all()
