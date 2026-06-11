"""ZIP bundle assembly (US-19 D-52)."""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from datetime import UTC, datetime

from app.domain.assets.content import compute_content_hash
from app.domain.export.manifest import build_manifest_v1
from app.domain.export.types import ExportBundleResult, ExportFileEntry
from app.infrastructure.storage.minio_client import MinioClient


async def build_export_zip(
    *,
    pipeline_run_id: uuid.UUID,
    project_id: uuid.UUID,
    entries: list[ExportFileEntry],
    minio: MinioClient,
) -> ExportBundleResult:
    """Load MinIO bytes, build manifest, assemble deterministic ZIP."""
    exported_at = datetime.now(tz=UTC)
    loaded: list[tuple[ExportFileEntry, bytes]] = []
    for entry in entries:
        data = await minio.download_bytes(entry.asset.minio_key)
        if compute_content_hash(data) != entry.asset.content_hash:
            raise ValueError(f"hash mismatch for {entry.zip_path}")
        loaded.append((entry, data))

    manifest = build_manifest_v1(
        pipeline_run_id=pipeline_run_id,
        project_id=project_id,
        exported_at=exported_at,
        file_entries=loaded,
    )
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_hash = compute_content_hash(manifest_bytes)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest_bytes)
        for entry, data in loaded:
            zf.writestr(entry.zip_path, data)

    zip_bytes = buffer.getvalue()
    return ExportBundleResult(
        zip_bytes=zip_bytes,
        manifest_json=manifest,
        manifest_hash=manifest_hash,
        file_count=len(loaded),
        pipeline_run_id=pipeline_run_id,
        project_id=project_id,
        exported_at=exported_at,
    )
