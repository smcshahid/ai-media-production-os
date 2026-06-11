"""manifest.json v1 builder (US-19 D-53)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.export.types import ExportFileEntry

MANIFEST_VERSION = "1"


def build_manifest_v1(
    *,
    pipeline_run_id: uuid.UUID,
    project_id: uuid.UUID,
    exported_at: datetime,
    file_entries: list[tuple[ExportFileEntry, bytes]],
) -> dict:
    """Build manifest dict from resolved entries and loaded bytes."""
    files = []
    for entry, data in file_entries:
        meta = entry.asset.metadata_json or {}
        file_obj: dict = {
            "path": entry.zip_path,
            "stage": entry.asset.stage.value,
            "version": entry.asset.version,
            "content_hash": entry.asset.content_hash,
            "approval_at": (
                entry.approval_at.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
                if entry.approval_at
                else None
            ),
            "asset_id": str(entry.asset.id),
            "size_bytes": len(data),
            "branch": entry.asset.branch,
        }
        if entry.asset.stage.value == "STORYBOARD":
            file_obj["frame_index"] = int(meta.get("frame_index", 0))
        model_id = meta.get("model_id")
        if model_id:
            file_obj["model_id"] = model_id
        files.append(file_obj)

    exported_iso = exported_at.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    return {
        "manifest_version": MANIFEST_VERSION,
        "pipeline_run_id": str(pipeline_run_id),
        "project_id": str(project_id),
        "exported_at": exported_iso,
        "files": files,
    }
