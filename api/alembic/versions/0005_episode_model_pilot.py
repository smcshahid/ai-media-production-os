"""Episode model pilot schema (Phase 6 / SCR-2026-004)

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-17

Additive only: episodes table, pipeline_runs.episode_id nullable FK.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "episodes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "IN_PROGRESS",
                "COMPLETED",
                "ARCHIVED",
                name="episodestatus",
                native_enum=False,
                length=16,
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "episode_number",
            name="uq_episodes_project_number",
        ),
    )
    op.create_index("ix_episodes_project_id", "episodes", ["project_id"])

    op.add_column(
        "pipeline_runs",
        sa.Column("episode_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_pipeline_runs_episode_id",
        "pipeline_runs",
        "episodes",
        ["episode_id"],
        ["id"],
    )
    op.create_index("ix_pipeline_runs_episode_id", "pipeline_runs", ["episode_id"])


def downgrade() -> None:
    op.drop_index("ix_pipeline_runs_episode_id", table_name="pipeline_runs")
    op.drop_constraint("fk_pipeline_runs_episode_id", "pipeline_runs", type_="foreignkey")
    op.drop_column("pipeline_runs", "episode_id")
    op.drop_index("ix_episodes_project_id", table_name="episodes")
    op.drop_table("episodes")
