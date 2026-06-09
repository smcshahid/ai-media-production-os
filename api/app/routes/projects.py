"""``GET /projects`` — list projects (US-01 / T-01-03).

For Sprint 0 this returns the single seeded "AIMPOS Spark Demo" project. The
response field is ``name`` (not ``title``) per the Sprint 0 plan §4.6 contract
and DECISIONS D-18. Pipeline-start and other project mutations are out of scope
(Sprint 1+).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_session
from app.infrastructure.db.repositories.project import ProjectRepository

router = APIRouter(tags=["projects"])


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str


@router.get("/projects", response_model=list[ProjectRead], summary="List projects")
async def list_projects(
    session: AsyncSession = Depends(get_session),
) -> list[ProjectRead]:
    projects = await ProjectRepository(session).list()
    return [ProjectRead.model_validate(project) for project in projects]
