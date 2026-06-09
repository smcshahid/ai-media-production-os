"""FastAPI application factory.

Owns the lifecycle of process-wide resources (DB engine, Redis, HTTP client) via
the lifespan context and parks them on ``app.state`` for the DI layer. Keep this
thin: routing and behaviour live in ``app/routes`` and the domain/infrastructure
packages.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from aimpos_config import configure_logging, get_settings
from fastapi import FastAPI

from app.infrastructure.cache.redis_client import build_redis
from app.infrastructure.db.session import build_engine
from app.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)

    app.state.settings = settings
    app.state.engine = build_engine(settings.database_url)
    app.state.redis = build_redis(settings.redis_url)
    app.state.http = httpx.AsyncClient()
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
    app.include_router(health_router)
    return app


app = create_app()
