"""Shared test fixtures.

The ``session`` fixture builds a fresh in-memory SQLite (async) database per
test and creates the full schema from the models. SQLite keeps repository tests
hermetic and fast (addresses the non-hermetic smell noted in TD-02/TD-08);
PostgreSQL-specific behaviour is covered by the compose integration tests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Base
from app.infrastructure.db.session import build_engine, build_sessionmaker


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = build_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = build_sessionmaker(engine)
    async with sessionmaker() as db_session:
        yield db_session
    await engine.dispose()
