"""Seed the default project (T-01-02).

Idempotent: creates the single "AIMPOS Spark Demo" project only when the
projects table is empty, so it is safe to run on every API startup and via
``make seed`` / ``python -m app.seed.default_project``. The default project's
identity comes from the domain (``app.domain.studio.project``).
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.studio.project import DEFAULT_PROJECT_NAME, DEFAULT_PROJECT_STATUS
from app.infrastructure.db.models.project import Project
from app.infrastructure.db.repositories.project import ProjectRepository

logger = logging.getLogger("aimpos.seed")


async def seed_default_project(session: AsyncSession) -> Project | None:
    """Create the default project if none exist. Returns it, or None if skipped."""
    repository = ProjectRepository(session)
    existing = await repository.list()
    if existing:
        logger.info("seed.default_project.skipped", extra={"existing_count": len(existing)})
        return None

    project = Project(name=DEFAULT_PROJECT_NAME, status=DEFAULT_PROJECT_STATUS)
    await repository.add(project)
    await session.commit()
    logger.info(
        "seed.default_project.created",
        extra={"project_id": str(project.id), "project_name": project.name},
    )
    return project


async def _main() -> None:
    # Standalone entrypoint (`make seed`): build a short-lived engine from
    # settings, seed, and dispose. Used after `make migrate` on a fresh stack.
    from aimpos_config import configure_logging, get_settings

    from app.infrastructure.db.session import build_engine, build_sessionmaker

    settings = get_settings()
    configure_logging(settings.log_level)
    engine = build_engine(settings.database_url)
    try:
        sessionmaker = build_sessionmaker(engine)
        async with sessionmaker() as session:
            await seed_default_project(session)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
