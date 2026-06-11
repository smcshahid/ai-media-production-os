"""STORYBOARD multi-frame batch unique indexes (US-16 / D-43)

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-11

D-43 shares one batch ``version`` across N STORYBOARD frames distinguished by
``metadata_json.frame_index``. The original (project_id, stage, version) unique
constraint allowed only one row per version; replace with stage-aware partial
indexes.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_asset_versions_project_id_stage_version",
        "asset_versions",
        type_="unique",
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_asset_versions_project_stage_version_single
        ON asset_versions (project_id, stage, version)
        WHERE stage != 'STORYBOARD'
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_asset_versions_storyboard_batch_frame
        ON asset_versions (project_id, stage, version, (metadata_json->>'frame_index'))
        WHERE stage = 'STORYBOARD'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_asset_versions_storyboard_batch_frame")
    op.execute("DROP INDEX IF EXISTS uq_asset_versions_project_stage_version_single")
    op.create_unique_constraint(
        "uq_asset_versions_project_id_stage_version",
        "asset_versions",
        ["project_id", "stage", "version"],
    )
