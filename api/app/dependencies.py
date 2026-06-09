"""FastAPI dependency-injection wiring.

Resources with a process lifetime (settings, DB engine, Redis, HTTP client) are
created once in the app factory and parked on ``app.state``; these providers
expose them to routes. ``get_health_checks`` is its own dependency so tests can
override it without standing up real PostgreSQL / Redis / MinIO.
"""

from __future__ import annotations

import asyncio

import httpx
from aimpos_config import Settings
from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from app.infrastructure.health.probes import (
    DependencyStatus,
    check_minio,
    check_postgres,
    check_redis,
)


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_engine(request: Request) -> AsyncEngine:
    engine: AsyncEngine = request.app.state.engine
    return engine


def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


def get_http_client(request: Request) -> httpx.AsyncClient:
    client: httpx.AsyncClient = request.app.state.http
    return client


async def get_health_checks(request: Request) -> dict[str, DependencyStatus]:
    """Run all dependency probes concurrently and map them by name."""
    settings = get_settings(request)
    postgres, redis_status, minio = await asyncio.gather(
        check_postgres(get_engine(request)),
        check_redis(get_redis(request)),
        check_minio(
            get_http_client(request),
            settings.minio_endpoint,
            secure=settings.minio_secure,
        ),
    )
    return {"postgresql": postgres, "redis": redis_status, "minio": minio}
