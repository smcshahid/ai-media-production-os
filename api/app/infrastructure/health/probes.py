"""Dependency health probes used by ``GET /health``.

Each probe is self-contained, bounded by a timeout, and never raises: a failure
is reported as ``DependencyStatus(status="error", ...)`` so the endpoint can
aggregate a single 200/503 verdict. Probes are intentionally lightweight
connectivity checks — the full MinIO/Redis clients land with their own stories
(US-05 and later); here we only prove reachability.
"""

from __future__ import annotations

import asyncio
from typing import Literal

import httpx
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

DEFAULT_TIMEOUT = 3.0


class DependencyStatus(BaseModel):
    """Health verdict for a single dependency."""

    status: Literal["ok", "error"]
    detail: str | None = None


async def check_postgres(engine: AsyncEngine, timeout: float = DEFAULT_TIMEOUT) -> DependencyStatus:
    """Probe PostgreSQL with a trivial ``SELECT 1``."""
    try:
        async with asyncio.timeout(timeout):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return DependencyStatus(status="ok")
    except Exception as exc:  # noqa: BLE001 — health must surface any failure as error
        return DependencyStatus(status="error", detail=str(exc))


async def check_redis(client: Redis, timeout: float = DEFAULT_TIMEOUT) -> DependencyStatus:
    """Probe Redis with ``PING``."""
    try:
        async with asyncio.timeout(timeout):
            await client.ping()
        return DependencyStatus(status="ok")
    except Exception as exc:  # noqa: BLE001 — health must surface any failure as error
        return DependencyStatus(status="error", detail=str(exc))


async def check_minio(
    client: httpx.AsyncClient,
    endpoint: str,
    *,
    secure: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> DependencyStatus:
    """Probe MinIO via its unauthenticated liveness endpoint."""
    scheme = "https" if secure else "http"
    url = f"{scheme}://{endpoint}/minio/health/live"
    try:
        response = await client.get(url, timeout=timeout)
        response.raise_for_status()
        return DependencyStatus(status="ok")
    except Exception as exc:  # noqa: BLE001 — health must surface any failure as error
        return DependencyStatus(status="error", detail=str(exc))
