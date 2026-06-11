"""Export bundle types (US-19 D-52 / D-53)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.infrastructure.db.models.asset_version import AssetVersion


@dataclass(frozen=True, slots=True)
class ExportFileEntry:
    """One asset row mapped to a deterministic ZIP path."""

    asset: AssetVersion
    zip_path: str
    approval_at: datetime | None


@dataclass(frozen=True, slots=True)
class ExportBundleResult:
    """Built ZIP plus manifest metadata for audit (D-54)."""

    zip_bytes: bytes
    manifest_json: dict
    manifest_hash: str
    file_count: int
    pipeline_run_id: uuid.UUID
    project_id: uuid.UUID
    exported_at: datetime
