"""Asset history response types (US-22 D-57)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AssetHistoryVersion(BaseModel):
    asset_id: uuid.UUID
    version: int
    content_hash: str
    is_ai_generated: bool
    branch: str
    pipeline_run_id: uuid.UUID | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class AssetHistoryStage(BaseModel):
    stage: str
    versions: list[AssetHistoryVersion]


class AssetHistoryResponse(BaseModel):
    project_id: uuid.UUID
    stages: list[AssetHistoryStage]
