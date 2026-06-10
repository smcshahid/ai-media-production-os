"""Asset application service — ``store_asset`` (T-05-03).

Lives in the domain (Repository Structure §"Asset Service → api/domain/assets/")
yet stays framework-free (coding-standards §Domain purity): it depends only on
the abstract ports below, which the infrastructure layer implements (MinIO client
and the asset-version repository) and the caller injects. This keeps SQLAlchemy
and the storage SDK out of the domain.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from aimpos_core.enums import AssetStage

from app.domain.assets.content import build_object_key, compute_content_hash


@dataclass(frozen=True, slots=True)
class StoredAsset:
    """Framework-free result of storing an asset version."""

    id: uuid.UUID
    project_id: uuid.UUID
    stage: AssetStage
    version: int
    minio_key: str
    content_hash: str
    is_ai_generated: bool
    branch: str
    metadata_json: dict | None = None


class BlobStore(Protocol):
    """Port for content storage (implemented by the MinIO adapter)."""

    async def upload_bytes(self, key: str, data: bytes, content_type: str) -> str: ...

    async def download_bytes(self, key: str) -> bytes: ...


class AssetVersionStore(Protocol):
    """Port for the asset-version metadata chain (implemented by the repository)."""

    async def next_version(self, project_id: uuid.UUID, stage: AssetStage) -> int: ...

    async def add_version(
        self,
        *,
        project_id: uuid.UUID,
        stage: AssetStage,
        version: int,
        minio_key: str,
        content_hash: str,
        is_ai_generated: bool,
        branch: str,
        metadata_json: dict | None = None,
    ) -> StoredAsset: ...


async def store_asset(
    *,
    data: bytes,
    stage: AssetStage,
    project_id: uuid.UUID,
    blobs: BlobStore,
    versions: AssetVersionStore,
    content_type: str = "application/octet-stream",
    is_ai_generated: bool = False,
    branch: str = "main",
    metadata_json: dict | None = None,
) -> StoredAsset:
    """Hash bytes, store the blob, and append a version row.

    Identical bytes reuse the same content-addressed key (blob dedup) but always
    produce a new version row along the ``(project, stage)`` chain.
    """
    content_hash = compute_content_hash(data)
    key = build_object_key(project_id, stage, content_hash)
    await blobs.upload_bytes(key, data, content_type)
    version = await versions.next_version(project_id, stage)
    return await versions.add_version(
        project_id=project_id,
        stage=stage,
        version=version,
        minio_key=key,
        content_hash=content_hash,
        is_ai_generated=is_ai_generated,
        branch=branch,
        metadata_json=metadata_json,
    )
