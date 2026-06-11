"""Sync asset load/store for worker activities (mirrors api ``store_asset`` semantics)."""

from __future__ import annotations

import hashlib
import io
import uuid
from dataclasses import dataclass

from aimpos_config import Settings
from aimpos_core.enums import AssetStage
from minio import Minio
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class AssetStoreError(Exception):
    """Asset persistence failed."""


class IdeaNotFoundError(AssetStoreError):
    """No IDEA asset exists for the project."""


class ApprovedStoryNotFoundError(AssetStoreError):
    """No approved STORY asset exists for the pipeline run (D-37)."""


class ApprovedScriptNotFoundError(AssetStoreError):
    """No approved SCRIPT asset exists for the pipeline run (D-41)."""


@dataclass(frozen=True, slots=True)
class IdeaAsset:
    project_id: uuid.UUID
    idea_text: str
    style_note: str | None
    minio_key: str


@dataclass(frozen=True, slots=True)
class StoredStoryAsset:
    asset_version_id: uuid.UUID
    content_hash: str
    minio_key: str
    version: int


@dataclass(frozen=True, slots=True)
class ApprovedStoryAsset:
    asset_version_id: uuid.UUID
    story_text: str
    minio_key: str
    version: int


@dataclass(frozen=True, slots=True)
class StoredScriptAsset:
    asset_version_id: uuid.UUID
    content_hash: str
    minio_key: str
    version: int


@dataclass(frozen=True, slots=True)
class ApprovedScriptAsset:
    asset_version_id: uuid.UUID
    script_fountain: str
    minio_key: str
    version: int


def _engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def _minio_client(settings: Settings) -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def compute_content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_object_key(project_id: uuid.UUID, stage: AssetStage, content_hash: str) -> str:
    return f"{project_id}/{stage.value}/{content_hash}"


def fetch_latest_idea(settings: Settings, project_id: uuid.UUID) -> IdeaAsset:
    """Return the newest IDEA version and download ``idea.txt`` bytes."""
    engine = _engine(settings)
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT minio_key, metadata_json
                    FROM asset_versions
                    WHERE project_id = :project_id AND stage = 'IDEA'
                    ORDER BY version DESC
                    LIMIT 1
                    """
                ),
                {"project_id": str(project_id)},
            ).mappings().first()
        if row is None:
            raise IdeaNotFoundError(f"no IDEA asset for project {project_id}")

        client = _minio_client(settings)
        response = client.get_object(settings.minio_bucket, row["minio_key"])
        try:
            data = response.read()
        finally:
            response.close()
            response.release_conn()
    finally:
        engine.dispose()

    metadata = row["metadata_json"] or {}
    style_note = metadata.get("style_note") if isinstance(metadata, dict) else None
    return IdeaAsset(
        project_id=project_id,
        idea_text=data.decode("utf-8"),
        style_note=str(style_note).strip() if style_note else None,
        minio_key=row["minio_key"],
    )


def store_story_markdown(
    settings: Settings,
    *,
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID,
    story_md: str,
    branch: str = "ai-draft",
) -> StoredStoryAsset:
    """Persist ``story.md`` as a new STORY version on the given branch."""
    data = story_md.encode("utf-8")
    content_hash = compute_content_hash(data)
    key = build_object_key(project_id, AssetStage.STORY, content_hash)
    client = _minio_client(settings)
    client.put_object(
        settings.minio_bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type="text/markdown",
    )

    engine = _engine(settings)
    try:
        with engine.begin() as conn:
            version = conn.execute(
                text(
                    """
                    SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                    FROM asset_versions
                    WHERE project_id = :project_id AND stage = 'STORY'
                    """
                ),
                {"project_id": str(project_id)},
            ).scalar_one()
            asset_id = uuid.uuid4()
            conn.execute(
                text(
                    """
                    INSERT INTO asset_versions (
                        id, project_id, pipeline_run_id, stage, version,
                        minio_key, content_hash, is_ai_generated, branch, metadata_json
                    ) VALUES (
                        :id, :project_id, :pipeline_run_id, 'STORY', :version,
                        :minio_key, :content_hash, TRUE, :branch, NULL
                    )
                    """
                ),
                {
                    "id": str(asset_id),
                    "project_id": str(project_id),
                    "pipeline_run_id": str(pipeline_run_id),
                    "version": version,
                    "minio_key": key,
                    "content_hash": content_hash,
                    "branch": branch,
                },
            )
    finally:
        engine.dispose()

    return StoredStoryAsset(
        asset_version_id=asset_id,
        content_hash=content_hash,
        minio_key=key,
        version=int(version),
    )


def fetch_approved_story(
    settings: Settings,
    *,
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID,
) -> ApprovedStoryAsset:
    """Return latest STORY version gated by APPROVED approval (D-37)."""
    engine = _engine(settings)
    try:
        with engine.begin() as conn:
            approved = conn.execute(
                text(
                    """
                    SELECT 1 FROM approvals
                    WHERE pipeline_run_id = :run_id
                      AND stage = 'STORY'
                      AND decision = 'APPROVED'
                    LIMIT 1
                    """
                ),
                {"run_id": str(pipeline_run_id)},
            ).first()
            if approved is None:
                raise ApprovedStoryNotFoundError(
                    f"no APPROVED STORY approval for run {pipeline_run_id}"
                )

            row = conn.execute(
                text(
                    """
                    SELECT id, minio_key, version
                    FROM asset_versions
                    WHERE project_id = :project_id AND stage = 'STORY'
                    ORDER BY version DESC
                    LIMIT 1
                    """
                ),
                {"project_id": str(project_id)},
            ).mappings().first()
        if row is None:
            raise ApprovedStoryNotFoundError(f"no STORY asset for project {project_id}")

        client = _minio_client(settings)
        response = client.get_object(settings.minio_bucket, row["minio_key"])
        try:
            data = response.read()
        finally:
            response.close()
            response.release_conn()
    finally:
        engine.dispose()

    return ApprovedStoryAsset(
        asset_version_id=uuid.UUID(str(row["id"])),
        story_text=data.decode("utf-8"),
        minio_key=row["minio_key"],
        version=int(row["version"]),
    )


def fetch_latest_script_rejection_rationale(
    settings: Settings,
    *,
    pipeline_run_id: uuid.UUID,
) -> str | None:
    """Return latest SCRIPT rejection note for regeneration (D-42)."""
    engine = _engine(settings)
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT rationale FROM approvals
                    WHERE pipeline_run_id = :run_id
                      AND stage = 'SCRIPT'
                      AND decision = 'REJECTED'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"run_id": str(pipeline_run_id)},
            ).first()
    finally:
        engine.dispose()
    if row is None or not row[0]:
        return None
    return str(row[0]).strip()


def fetch_approved_script(
    settings: Settings,
    *,
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID,
) -> ApprovedScriptAsset:
    """Return latest SCRIPT version gated by APPROVED approval (D-41)."""
    engine = _engine(settings)
    try:
        with engine.begin() as conn:
            approved = conn.execute(
                text(
                    """
                    SELECT 1 FROM approvals
                    WHERE pipeline_run_id = :run_id
                      AND stage = 'SCRIPT'
                      AND decision = 'APPROVED'
                    LIMIT 1
                    """
                ),
                {"run_id": str(pipeline_run_id)},
            ).first()
            if approved is None:
                raise ApprovedScriptNotFoundError(
                    f"no APPROVED SCRIPT approval for run {pipeline_run_id}"
                )

            row = conn.execute(
                text(
                    """
                    SELECT id, minio_key, version
                    FROM asset_versions
                    WHERE project_id = :project_id AND stage = 'SCRIPT'
                    ORDER BY version DESC
                    LIMIT 1
                    """
                ),
                {"project_id": str(project_id)},
            ).mappings().first()
        if row is None:
            raise ApprovedScriptNotFoundError(f"no SCRIPT asset for project {project_id}")

        client = _minio_client(settings)
        response = client.get_object(settings.minio_bucket, row["minio_key"])
        try:
            data = response.read()
        finally:
            response.close()
            response.release_conn()
    finally:
        engine.dispose()

    return ApprovedScriptAsset(
        asset_version_id=uuid.UUID(str(row["id"])),
        script_fountain=data.decode("utf-8"),
        minio_key=row["minio_key"],
        version=int(row["version"]),
    )


def store_script_fountain(
    settings: Settings,
    *,
    project_id: uuid.UUID,
    pipeline_run_id: uuid.UUID,
    script_fountain: str,
    branch: str = "ai-draft",
) -> StoredScriptAsset:
    """Persist ``script.fountain`` as a new SCRIPT version (D-39)."""
    data = script_fountain.encode("utf-8")
    content_hash = compute_content_hash(data)
    key = build_object_key(project_id, AssetStage.SCRIPT, content_hash)
    client = _minio_client(settings)
    client.put_object(
        settings.minio_bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type="text/plain; charset=utf-8",
    )

    engine = _engine(settings)
    try:
        with engine.begin() as conn:
            version = conn.execute(
                text(
                    """
                    SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                    FROM asset_versions
                    WHERE project_id = :project_id AND stage = 'SCRIPT'
                    """
                ),
                {"project_id": str(project_id)},
            ).scalar_one()
            asset_id = uuid.uuid4()
            conn.execute(
                text(
                    """
                    INSERT INTO asset_versions (
                        id, project_id, pipeline_run_id, stage, version,
                        minio_key, content_hash, is_ai_generated, branch, metadata_json
                    ) VALUES (
                        :id, :project_id, :pipeline_run_id, 'SCRIPT', :version,
                        :minio_key, :content_hash, TRUE, :branch, NULL
                    )
                    """
                ),
                {
                    "id": str(asset_id),
                    "project_id": str(project_id),
                    "pipeline_run_id": str(pipeline_run_id),
                    "version": version,
                    "minio_key": key,
                    "content_hash": content_hash,
                    "branch": branch,
                },
            )
    finally:
        engine.dispose()

    return StoredScriptAsset(
        asset_version_id=asset_id,
        content_hash=content_hash,
        minio_key=key,
        version=int(version),
    )


def insert_lineage_edge(
    settings: Settings,
    *,
    parent_id: uuid.UUID,
    child_id: uuid.UUID,
) -> None:
    """Record parent→child provenance in ``lineage_edges``."""
    engine = _engine(settings)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO lineage_edges (id, parent_id, child_id)
                    VALUES (:id, :parent_id, :child_id)
                    ON CONFLICT (parent_id, child_id) DO NOTHING
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "parent_id": str(parent_id),
                    "child_id": str(child_id),
                },
            )
    finally:
        engine.dispose()
