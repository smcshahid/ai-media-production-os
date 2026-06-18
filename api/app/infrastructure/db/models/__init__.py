"""SQLAlchemy ORM models for the six MVP core tables (MVP Definition §6.5).

Importing this package registers every table on ``Base.metadata`` so that
Alembic autogenerate (T-04-02) and ``create_all`` see the full schema.
"""

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.approval import Approval
from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.audit_event import AuditEvent
from app.infrastructure.db.models.character import Character
from app.infrastructure.db.models.episode import Episode
from app.infrastructure.db.models.lineage_edge import LineageEdge
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.models.project import Project

__all__ = [
    "Base",
    "Approval",
    "AssetVersion",
    "AuditEvent",
    "Character",
    "Episode",
    "LineageEdge",
    "PipelineRun",
    "Project",
]
