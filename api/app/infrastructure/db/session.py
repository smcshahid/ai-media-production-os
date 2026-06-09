"""Async SQLAlchemy session plumbing.

Pure builders only — no global engine and no environment reads here. The
application wires these to settings in the app factory / DI layer (US-03,
``aimpos-config``); tests build an engine against a throwaway database. This
keeps the persistence layer dependency-injected and framework-light.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def build_engine(url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async engine for the given SQLAlchemy URL.

    Use an async driver, e.g. ``postgresql+psycopg://…`` (psycopg 3 supports
    async) in production or ``sqlite+aiosqlite://…`` in tests.
    """

    return create_async_engine(url, echo=echo, pool_pre_ping=True)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to ``engine``.

    ``expire_on_commit=False`` keeps ORM objects usable after commit, which
    suits request/response and activity boundaries.
    """

    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
