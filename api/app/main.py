"""FastAPI application factory.

Owns the lifecycle of process-wide resources (DB engine, Redis, HTTP client) via
the lifespan context and parks them on ``app.state`` for the DI layer. Keep this
thin: routing and behaviour live in ``app/routes`` and the domain/infrastructure
packages.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from aimpos_config import configure_logging, get_settings
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.cache.redis_client import build_redis
from app.infrastructure.db.session import build_engine, build_sessionmaker
from app.infrastructure.storage.minio_client import MinioClient
from app.middleware.logging import AccessLogMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.routes.assets import router as assets_router
from app.routes.health import router as health_router
from app.routes.projects import router as projects_router
from app.seed.default_project import seed_default_project


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)

    app.state.settings = settings
    app.state.engine = build_engine(settings.database_url)
    app.state.sessionmaker = build_sessionmaker(app.state.engine)
    app.state.redis = build_redis(settings.redis_url)
    app.state.http = httpx.AsyncClient()
    app.state.minio = MinioClient.from_settings(settings)

    # Idempotent default-project seed (US-01). Tolerate a not-yet-migrated
    # schema so the API still boots and /health stays serviceable; the operator
    # runs `make migrate` then `make seed` (or restarts) on a fresh stack.
    try:
        async with app.state.sessionmaker() as session:
            await seed_default_project(session)
    except SQLAlchemyError as exc:
        logging.getLogger("aimpos.seed").warning(
            "seed.default_project.deferred", extra={"error": str(exc)}
        )

    try:
        yield
    finally:
        await app.state.http.aclose()
        await app.state.redis.aclose()
        await app.state.engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AIMPOS-Spark Visual API",
        version="0.1.0",
        summary="Governed AI media production platform — REST surface.",
        lifespan=lifespan,
    )
    # Order matters: middleware added last runs outermost. RequestID must wrap
    # AccessLog so the request_id context var is set before the access line is
    # emitted (and is available to the handler in between).
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(assets_router)
    return app


app = create_app()
