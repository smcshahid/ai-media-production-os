"""Lineage response types (US-20 D-55)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class LineageNode(BaseModel):
    asset_id: uuid.UUID
    stage: str
    version: int
    content_hash: str
    is_ai_generated: bool
    branch: str
    metadata: dict = Field(default_factory=dict)
    parent_asset_ids: list[uuid.UUID] = Field(default_factory=list)
    synthetic: bool | None = None


class LineageEdgeOut(BaseModel):
    parent_asset_id: uuid.UUID
    child_asset_id: uuid.UUID


class LineageResponse(BaseModel):
    pipeline_run_id: uuid.UUID
    project_id: uuid.UUID
    nodes: list[LineageNode]
    edges: list[LineageEdgeOut]
