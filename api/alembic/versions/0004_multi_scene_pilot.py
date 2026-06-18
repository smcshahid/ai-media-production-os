"""Multi-scene pilot schema (Phase 4 / SCR-2026-002)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-17

Additive only: pipeline run scene tracking, approval scene_index,
STORYBOARD unique index extended with scene_index in metadata.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pipeline_runs",
        sa.Column("scene_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "pipeline_runs",
        sa.Column("current_scene_index", sa.Integer(), nullable=True),
    )
    op.add_column(
        "approvals",
        sa.Column("scene_index", sa.Integer(), nullable=True),
    )

    op.execute("DROP INDEX IF EXISTS uq_asset_versions_storyboard_batch_frame")
    op.execute(
        """
        CREATE UNIQUE INDEX uq_asset_versions_storyboard_batch_scene_frame
        ON asset_versions (
            project_id,
            stage,
            version,
            COALESCE(metadata_json->>'scene_index', '1'),
            (metadata_json->>'frame_index')
        )
        WHERE stage = 'STORYBOARD'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_asset_versions_storyboard_batch_scene_frame")
    op.execute(
        """
        CREATE UNIQUE INDEX uq_asset_versions_storyboard_batch_frame
        ON asset_versions (project_id, stage, version, (metadata_json->>'frame_index'))
        WHERE stage = 'STORYBOARD'
        """
    )

    op.drop_column("approvals", "scene_index")
    op.drop_column("pipeline_runs", "current_scene_index")
    op.drop_column("pipeline_runs", "scene_count")
