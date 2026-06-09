"""Content-addressable hashing and object-key generation (T-05-02).

Pure functions — no I/O, no framework imports. The object key is deterministic in
``(project_id, stage, content_hash)`` so identical bytes for the same project and
stage always map to the same MinIO key (blob dedup), while each upload still gets
its own ``asset_versions`` row.
"""

from __future__ import annotations

import hashlib
import uuid

from aimpos_core.enums import AssetStage


def compute_content_hash(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data`` (content address)."""
    return hashlib.sha256(data).hexdigest()


def build_object_key(project_id: uuid.UUID, stage: AssetStage, content_hash: str) -> str:
    """Build the deterministic MinIO object key ``{project_id}/{stage}/{content_hash}``."""
    return f"{project_id}/{stage.value}/{content_hash}"
