"""``projects`` — Studio Governance aggregate root (BC: Studio & Project)."""

from __future__ import annotations

import uuid
from datetime import datetime

from aimpos_core.enums import ProjectStatus
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base, created_at_column, uuid_pk


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False, length=16),
        nullable=False,
        default=ProjectStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = created_at_column()
