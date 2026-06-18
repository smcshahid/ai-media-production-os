"""manifest.json builder (US-19 D-53 / Phase 4 v2 / Phase 5 v3 / Phase 6 v4)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from aimpos_core.scene import scene_index_from_metadata

from app.domain.export.types import ExportFileEntry

MANIFEST_VERSION_V1 = "1"
MANIFEST_VERSION_V2 = "2"
MANIFEST_VERSION_V3 = "3"
MANIFEST_VERSION_V4 = "4"
MANIFEST_VERSION_V5 = "5"


def _has_narration_entries(file_entries: list[tuple[ExportFileEntry, bytes]]) -> bool:
    for entry, _data in file_entries:
        if entry.asset.stage.value == "NARRATION":
            return True
        if entry.asset.stage.value == "VIDEO":
            meta = entry.asset.metadata_json or {}
            if meta.get("has_narration") is True:
                return True
    return False


def _manifest_version_for_entries(
    file_entries: list[tuple[ExportFileEntry, bytes]],
    *,
    episode_number: int | None = None,
    has_characters: bool = False,
) -> str:
    if has_characters:
        return MANIFEST_VERSION_V5
    if episode_number is not None:
        return MANIFEST_VERSION_V4
    if _has_narration_entries(file_entries):
        return MANIFEST_VERSION_V3
    for entry, _data in file_entries:
        if entry.zip_path.startswith("scenes/"):
            return MANIFEST_VERSION_V2
        meta = entry.asset.metadata_json or {}
        if scene_index_from_metadata(meta) > 1 or meta.get("scene_count", 1) not in (1, "1", None):
            if int(meta.get("scene_count", 1) or 1) > 1:
                return MANIFEST_VERSION_V2
    return MANIFEST_VERSION_V1


def build_manifest(
    *,
    pipeline_run_id: uuid.UUID,
    project_id: uuid.UUID,
    exported_at: datetime,
    file_entries: list[tuple[ExportFileEntry, bytes]],
    scene_count: int | None = None,
    episode_id: uuid.UUID | None = None,
    episode_number: int | None = None,
    characters: list[dict[str, str | None]] | None = None,
) -> dict:
    """Build manifest dict from resolved entries and loaded bytes."""
    has_characters = bool(characters)
    manifest_version = _manifest_version_for_entries(
        file_entries, episode_number=episode_number, has_characters=has_characters
    )
    has_narration = _has_narration_entries(file_entries)
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
            file_obj["scene_index"] = scene_index_from_metadata(meta)
        if entry.asset.stage.value in ("VIDEO", "NARRATION"):
            file_obj["scene_index"] = scene_index_from_metadata(meta)
        if episode_number is not None:
            file_obj["episode_number"] = episode_number
        if entry.asset.stage.value == "VIDEO":
            if meta.get("has_narration") is True:
                file_obj["has_narration"] = True
            narration_source = meta.get("narration_source")
            if narration_source:
                file_obj["narration_source"] = narration_source
        if entry.asset.stage.value == "NARRATION":
            tts_source = meta.get("tts_source")
            if tts_source:
                file_obj["tts_source"] = tts_source
            duration = meta.get("duration_sec") or meta.get("narration_duration_sec")
            if duration is not None:
                file_obj["duration_sec"] = duration
        model_id = meta.get("model_id")
        if model_id:
            file_obj["model_id"] = model_id
        files.append(file_obj)

    exported_iso = exported_at.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    payload: dict = {
        "manifest_version": manifest_version,
        "pipeline_run_id": str(pipeline_run_id),
        "project_id": str(project_id),
        "exported_at": exported_iso,
        "files": files,
    }
    if scene_count is not None and scene_count > 1:
        payload["scene_count"] = scene_count
    if has_narration:
        payload["narration_enabled"] = True
    if episode_id is not None and episode_number is not None:
        payload["episode_id"] = str(episode_id)
        payload["episode_number"] = episode_number
    if characters:
        payload["characters"] = characters
    return payload


def build_manifest_v1(
    *,
    pipeline_run_id: uuid.UUID,
    project_id: uuid.UUID,
    exported_at: datetime,
    file_entries: list[tuple[ExportFileEntry, bytes]],
) -> dict:
    """Backward-compatible v1 manifest builder."""
    manifest = build_manifest(
        pipeline_run_id=pipeline_run_id,
        project_id=project_id,
        exported_at=exported_at,
        file_entries=file_entries,
    )
    manifest["manifest_version"] = MANIFEST_VERSION_V1
    return manifest
