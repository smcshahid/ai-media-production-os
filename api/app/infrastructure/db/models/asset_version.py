"""``asset_versions`` — immutable, content-addressable outputs (BC: Asset & Provenance).

Field names follow MVP Definition §6.5 and T-04-01 AC: ``stage``, ``version``,
``minio_key``, ``content_hash``, ``is_ai_generated``, ``branch``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import AssetStage
from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, created_at_column, uuid_pk


class AssetVersion(Base):
    __tablename__ = "asset_versions"
    # Uniqueness: single-row stages use (project_id, stage, version); STORYBOARD
    # batches share version with per-frame ``metadata_json.frame_index`` (D-43).
    # Enforced by partial indexes in migration 0003 — not declarable on SQLite.
    __table_args__ = ()

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    # Human uploads (US-05) have no run; agent outputs reference their run.
    pipeline_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=True, index=True
    )
    stage: Mapped[AssetStage] = mapped_column(
        Enum(AssetStage, native_enum=False, length=16), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    minio_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    branch: Mapped[str] = mapped_column(String(64), nullable=False, default="main")
    # Optional stage-specific metadata (US-11 style_note; future agent fields).
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = created_at_column()
