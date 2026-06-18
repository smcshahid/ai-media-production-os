"""Repository for Character aggregate."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from aimpos_core.enums import PipelineRunStatus
from sqlalchemy import func, select

from app.infrastructure.db.models.character import Character
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.base import SQLAlchemyRepository

_ACTIVE_RUN_STATUSES = (
    PipelineRunStatus.PENDING,
    PipelineRunStatus.RUNNING,
    PipelineRunStatus.AWAITING_APPROVAL,
)


class CharacterRepository(SQLAlchemyRepository[Character]):
    model = Character

    async def list_for_project(self, project_id: uuid.UUID) -> Sequence[Character]:
        result = await self.session.execute(
            select(Character)
            .where(Character.project_id == project_id)
            .order_by(Character.created_at.asc(), Character.name.asc())
        )
        return result.scalars().all()

    async def count_for_project(self, project_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Character)
            .where(Character.project_id == project_id)
        )
        return int(result.scalar_one())

    async def get_for_project(
        self, project_id: uuid.UUID, character_id: uuid.UUID
    ) -> Character | None:
        result = await self.session.execute(
            select(Character).where(
                Character.project_id == project_id,
                Character.id == character_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_ids(
        self, project_id: uuid.UUID, character_ids: list[uuid.UUID]
    ) -> Sequence[Character]:
        if not character_ids:
            return []
        result = await self.session.execute(
            select(Character)
            .where(
                Character.project_id == project_id,
                Character.id.in_(character_ids),
            )
            .order_by(Character.name.asc())
        )
        return result.scalars().all()

    async def delete(self, character: Character) -> None:
        await self.session.delete(character)
        await self.session.flush()

    async def is_bound_to_active_run(
        self, project_id: uuid.UUID, character_id: uuid.UUID
    ) -> bool:
        result = await self.session.execute(
            select(PipelineRun).where(
                PipelineRun.project_id == project_id,
                PipelineRun.status.in_(_ACTIVE_RUN_STATUSES),
                PipelineRun.character_ids.isnot(None),
            )
        )
        cid = str(character_id)
        for run in result.scalars():
            ids = run.character_ids or []
            if cid in [str(x) for x in ids]:
                return True
        return False
