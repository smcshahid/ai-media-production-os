"""Unit tests for the /health endpoint and dependency probes.

The route tests override ``get_health_checks`` so no real PostgreSQL / Redis /
MinIO is needed; the probe tests exercise each probe in isolation with offline
fakes (in-memory SQLite, httpx MockTransport, a stub Redis).
"""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_health_checks
from app.infrastructure.db.session import build_engine
from app.infrastructure.health.probes import (
    DependencyStatus,
    check_minio,
    check_postgres,
    check_redis,
)
from app.main import create_app


def _client(checks: dict[str, DependencyStatus]) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_health_checks] = lambda: checks
    return TestClient(app)


def test_health_returns_200_when_all_dependencies_ok() -> None:
    checks = {name: DependencyStatus(status="ok") for name in ("postgresql", "redis", "minio")}
    with _client(checks) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert set(body["dependencies"]) == {"postgresql", "redis", "minio"}
    assert all(dep["status"] == "ok" for dep in body["dependencies"].values())


def test_health_returns_503_when_a_dependency_is_down() -> None:
    checks = {
        "postgresql": DependencyStatus(status="error", detail="connection refused"),
        "redis": DependencyStatus(status="ok"),
        "minio": DependencyStatus(status="ok"),
    }
    with _client(checks) as client:
        response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    assert body["dependencies"]["postgresql"]["status"] == "error"
    assert body["dependencies"]["postgresql"]["detail"] == "connection refused"


def test_health_is_registered_in_openapi() -> None:
    schema = create_app().openapi()
    assert "/health" in schema["paths"]
    assert "get" in schema["paths"]["/health"]


@pytest.mark.asyncio
async def test_check_postgres_ok_on_reachable_engine() -> None:
    engine = build_engine("sqlite+aiosqlite:///:memory:")
    try:
        result = await check_postgres(engine)
    finally:
        await engine.dispose()
    assert result.status == "ok"


@pytest.mark.asyncio
async def test_check_minio_ok_and_error() -> None:
    ok_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    bad_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(503)))
    try:
        ok = await check_minio(ok_client, "minio:9000")
        bad = await check_minio(bad_client, "minio:9000")
    finally:
        await ok_client.aclose()
        await bad_client.aclose()
    assert ok.status == "ok"
    assert bad.status == "error"


@pytest.mark.asyncio
async def test_check_redis_ok_and_error() -> None:
    class _PingOk:
        async def ping(self) -> bool:
            return True

    class _PingFails:
        async def ping(self) -> bool:
            raise ConnectionError("redis down")

    ok = await check_redis(_PingOk())  # type: ignore[arg-type]
    bad = await check_redis(_PingFails())  # type: ignore[arg-type]
    assert ok.status == "ok"
    assert bad.status == "error"
    assert bad.detail is not None
