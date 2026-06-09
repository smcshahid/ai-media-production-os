"""initial core tables

Revision ID: 0001
Revises:
Create Date: 2026-06-09 12:30:03.545476
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The six MVP core tables (MVP Definition §6.5). Generated from the
    # SQLAlchemy models (T-04-01) and reviewed; constraint names come from the
    # naming convention on Base.metadata (D-19).
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ARCHIVED", name="projectstatus", native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "RUNNING",
                "AWAITING_APPROVAL",
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                name="pipelinerunstatus",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column(
            "current_stage",
            sa.Enum(
                "IDEA",
                "STORY",
                "SCRIPT",
                "STORYBOARD",
                name="pipelinestage",
                native_enum=False,
                length=16,
            ),
            nullable=True,
        ),
        sa.Column("temporal_workflow_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_pipeline_runs_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_runs")),
        sa.UniqueConstraint(
            "temporal_workflow_id", name=op.f("uq_pipeline_runs_temporal_workflow_id")
        ),
    )
    op.create_index(
        op.f("ix_pipeline_runs_project_id"), "pipeline_runs", ["project_id"], unique=False
    )
    op.create_table(
        "asset_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_run_id", sa.Uuid(), nullable=True),
        sa.Column(
            "stage",
            sa.Enum(
                "IDEA",
                "STORY",
                "SCRIPT",
                "STORYBOARD",
                name="assetstage",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("minio_key", sa.String(length=1024), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False),
        sa.Column("branch", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["pipeline_run_id"],
            ["pipeline_runs.id"],
            name=op.f("fk_asset_versions_pipeline_run_id_pipeline_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_asset_versions_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asset_versions")),
        sa.UniqueConstraint(
            "project_id",
            "stage",
            "version",
            name=op.f("uq_asset_versions_project_id_stage_version"),
        ),
    )
    op.create_index(
        op.f("ix_asset_versions_content_hash"), "asset_versions", ["content_hash"], unique=False
    )
    op.create_index(
        op.f("ix_asset_versions_pipeline_run_id"),
        "asset_versions",
        ["pipeline_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_asset_versions_project_id"), "asset_versions", ["project_id"], unique=False
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("pipeline_run_id", sa.Uuid(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "PIPELINE_STARTED",
                "STAGE_STARTED",
                "STAGE_COMPLETED",
                "AGENT_TASK_COMPLETED",
                "APPROVAL_RECORDED",
                "ASSET_STORED",
                "PIPELINE_COMPLETED",
                "PIPELINE_FAILED",
                name="auditeventtype",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("model_id", sa.String(length=255), nullable=True),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["pipeline_run_id"],
            ["pipeline_runs.id"],
            name=op.f("fk_audit_events_pipeline_run_id_pipeline_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], name=op.f("fk_audit_events_project_id_projects")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(
        op.f("ix_audit_events_pipeline_run_id"), "audit_events", ["pipeline_run_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_events_project_id"), "audit_events", ["project_id"], unique=False
    )
    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_run_id", sa.Uuid(), nullable=False),
        sa.Column("asset_version_id", sa.Uuid(), nullable=True),
        sa.Column(
            "stage",
            sa.Enum(
                "IDEA",
                "STORY",
                "SCRIPT",
                "STORYBOARD",
                name="pipelinestage",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.Enum("APPROVED", "REJECTED", name="approvaldecision", native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_version_id"],
            ["asset_versions.id"],
            name=op.f("fk_approvals_asset_version_id_asset_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["pipeline_run_id"],
            ["pipeline_runs.id"],
            name=op.f("fk_approvals_pipeline_run_id_pipeline_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approvals")),
    )
    op.create_index(
        op.f("ix_approvals_pipeline_run_id"), "approvals", ["pipeline_run_id"], unique=False
    )
    op.create_table(
        "lineage_edges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["child_id"],
            ["asset_versions.id"],
            name=op.f("fk_lineage_edges_child_id_asset_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["asset_versions.id"],
            name=op.f("fk_lineage_edges_parent_id_asset_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lineage_edges")),
        sa.UniqueConstraint(
            "parent_id", "child_id", name=op.f("uq_lineage_edges_parent_id_child_id")
        ),
    )
    op.create_index(op.f("ix_lineage_edges_child_id"), "lineage_edges", ["child_id"], unique=False)
    op.create_index(
        op.f("ix_lineage_edges_parent_id"), "lineage_edges", ["parent_id"], unique=False
    )


def downgrade() -> None:
    # Drop in reverse dependency order so foreign keys resolve cleanly.
    op.drop_index(op.f("ix_lineage_edges_parent_id"), table_name="lineage_edges")
    op.drop_index(op.f("ix_lineage_edges_child_id"), table_name="lineage_edges")
    op.drop_table("lineage_edges")
    op.drop_index(op.f("ix_approvals_pipeline_run_id"), table_name="approvals")
    op.drop_table("approvals")
    op.drop_index(op.f("ix_audit_events_project_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_pipeline_run_id"), table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index(op.f("ix_asset_versions_project_id"), table_name="asset_versions")
    op.drop_index(op.f("ix_asset_versions_pipeline_run_id"), table_name="asset_versions")
    op.drop_index(op.f("ix_asset_versions_content_hash"), table_name="asset_versions")
    op.drop_table("asset_versions")
    op.drop_index(op.f("ix_pipeline_runs_project_id"), table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
    op.drop_table("projects")
