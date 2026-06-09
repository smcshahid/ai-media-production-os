"""Content hash + object key tests (T-05-02)."""

from __future__ import annotations

import hashlib
import uuid

from aimpos_core.enums import AssetStage

from app.domain.assets.content import build_object_key, compute_content_hash


def test_content_hash_matches_sha256_for_empty_small_large() -> None:
    for payload in (b"", b"hello", b"x" * 2_000_000):
        assert compute_content_hash(payload) == hashlib.sha256(payload).hexdigest()


def test_content_hash_is_deterministic_and_distinct() -> None:
    assert compute_content_hash(b"alpha") == compute_content_hash(b"alpha")
    assert compute_content_hash(b"alpha") != compute_content_hash(b"beta")
    assert len(compute_content_hash(b"anything")) == 64


def test_build_object_key_is_deterministic_and_formatted() -> None:
    project_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    content_hash = compute_content_hash(b"data")

    key = build_object_key(project_id, AssetStage.IDEA, content_hash)
    assert key == f"{project_id}/IDEA/{content_hash}"
    assert build_object_key(project_id, AssetStage.IDEA, content_hash) == key
