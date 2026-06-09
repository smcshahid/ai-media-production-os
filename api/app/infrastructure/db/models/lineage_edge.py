"""``lineage_edges`` — simple parent->child provenance in PostgreSQL (ADR-0003).

No Neo4j in the MVP: lineage is modelled as directed edges between asset
versions (MVP Definition §6.5).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, created_at_column, uuid_pk


class LineageEdge(Base):
    __tablename__ = "lineage_edges"
    __table_args__ = (UniqueConstraint("parent_id", "child_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asset_versions.id"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asset_versions.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = created_at_column()
