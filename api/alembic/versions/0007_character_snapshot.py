"""Character snapshot at pipeline start (Phase 7.5 / TD-P7-01)

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-18

Additive: pipeline_runs.character_snapshot JSON — export-time reproducibility.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pipeline_runs",
        sa.Column("character_snapshot", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pipeline_runs", "character_snapshot")
