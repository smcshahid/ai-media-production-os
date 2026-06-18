"""Character bible pilot schema (Phase 7 / SCR-2026-005)

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-18

Additive only: characters table, pipeline_runs.character_ids JSON.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "characters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("visual_traits", sa.Text(), nullable=True),
        sa.Column("personality_notes", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("project_id", "name", name="uq_characters_project_name"),
    )
    op.create_index("ix_characters_project_id", "characters", ["project_id"])

    op.add_column(
        "pipeline_runs",
        sa.Column("character_ids", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pipeline_runs", "character_ids")
    op.drop_index("ix_characters_project_id", table_name="characters")
    op.drop_table("characters")
