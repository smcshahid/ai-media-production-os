"""Manifest v5 character export tests (Phase 7)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.export.manifest import MANIFEST_VERSION_V5, build_manifest
from app.domain.export.types import ExportFileEntry


class _FakeAsset:
    def __init__(self, stage: str, metadata: dict | None = None) -> None:
        self.id = uuid.uuid4()
        self.stage = type("S", (), {"value": stage})()
        self.version = 1
        self.content_hash = "abc"
        self.branch = "main"
        self.metadata_json = metadata or {}


def test_manifest_v5_includes_characters() -> None:
    entry = ExportFileEntry(
        asset=_FakeAsset("IDEA"),
        zip_path="idea.txt",
        approval_at=None,
    )
    characters = [
        {
            "id": str(uuid.uuid4()),
            "name": "Maya",
            "role": "protagonist",
            "description": "Biologist",
            "visual_traits": "Lab coat",
            "personality_notes": "Curious",
        }
    ]
    manifest = build_manifest(
        pipeline_run_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        exported_at=datetime.now(tz=UTC),
        file_entries=[(entry, b"idea")],
        episode_id=uuid.uuid4(),
        episode_number=1,
        characters=characters,
    )
    assert manifest["manifest_version"] == MANIFEST_VERSION_V5
    assert manifest["characters"] == characters
    assert manifest["episode_number"] == 1


def test_manifest_v4_without_characters() -> None:
    entry = ExportFileEntry(
        asset=_FakeAsset("IDEA"),
        zip_path="idea.txt",
        approval_at=None,
    )
    manifest = build_manifest(
        pipeline_run_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        exported_at=datetime.now(tz=UTC),
        file_entries=[(entry, b"idea")],
        episode_id=uuid.uuid4(),
        episode_number=1,
        characters=None,
    )
    assert manifest["manifest_version"] == "4"
    assert "characters" not in manifest
