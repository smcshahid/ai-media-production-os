"""``GET /health`` — aggregated dependency liveness.

Returns 200 when every probed dependency is reachable, otherwise 503, with a
per-dependency breakdown so an operator can see *which* service is down. The
endpoint is part of the OpenAPI schema (both the 200 and 503 shapes).
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from app.dependencies import get_health_checks
from app.infrastructure.health.probes import DependencyStatus

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    dependencies: dict[str, DependencyStatus]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service and dependency health",
    responses={
        status.HTTP_200_OK: {"description": "All dependencies reachable"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthResponse,
            "description": "At least one dependency is unreachable",
        },
    },
)
async def health(
    response: Response,
    checks: dict[str, DependencyStatus] = Depends(get_health_checks),
) -> HealthResponse:
    healthy = all(check.status == "ok" for check in checks.values())
    response.status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="healthy" if healthy else "unhealthy",
        dependencies=checks,
    )
