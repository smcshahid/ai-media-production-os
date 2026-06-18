"""Episode aggregate — Phase 6 episode model pilot (SCR-2026-004)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import EpisodeStatus
from sqlalchemy import Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, created_at_column, uuid_pk


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[EpisodeStatus] = mapped_column(
        Enum(EpisodeStatus, native_enum=False, length=16),
        nullable=False,
        default=EpisodeStatus.DRAFT,
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
