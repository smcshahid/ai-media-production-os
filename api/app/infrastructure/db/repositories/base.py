"""Repository interface (port) and a generic async SQLAlchemy implementation.

The ``Repository`` Protocol is the abstraction that domain/application code
depends on; ``SQLAlchemyRepository`` is the concrete adapter. Both live under
``infrastructure/db/`` per Repository Structure §4.4 and coding-standards §33
(SQLAlchemy never leaks into ``app/domain/``).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Generic, Protocol, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Protocol[ModelT]):
    """Minimal persistence port shared by every aggregate-root repository."""

    async def add(self, entity: ModelT) -> ModelT: ...

    async def get(self, entity_id: uuid.UUID) -> ModelT | None: ...

    async def list(self) -> Sequence[ModelT]: ...


class SQLAlchemyRepository(Generic[ModelT]):
    """Generic async repository over a single ORM model.

    Subclasses set the ``model`` class attribute. Methods ``flush`` rather than
    ``commit`` so the caller (a unit of work / request scope) controls
    transaction boundaries.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self) -> Sequence[ModelT]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()
