"""Export orchestration (US-19)."""

from __future__ import annotations

import uuid

from aimpos_core.enums import PipelineRunStatus
from aimpos_core.events import AuditEventType
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.export.bundle import build_export_zip
from app.domain.export.resolver import ExportAssetResolutionError, resolve_export_files
from app.domain.export.types import ExportBundleResult
from app.infrastructure.db.models.audit_event import AuditEvent
from app.domain.character.service import load_characters_for_export
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
from app.infrastructure.db.repositories.audit_event import AuditEventRepository
from app.infrastructure.db.repositories.episode import EpisodeRepository
from app.infrastructure.db.repositories.pipeline_run import PipelineRunRepository
from app.infrastructure.storage.minio_client import MinioClient


class ExportNotFoundError(Exception):
    """Pipeline run does not exist."""


class ExportNotCompletedError(Exception):
    """Pipeline run is not COMPLETED."""


async def export_pipeline_run(
    pipeline_run_id: uuid.UUID,
    *,
    session: AsyncSession,
    minio: MinioClient,
) -> ExportBundleResult:
    """Build export ZIP and append BUNDLE_EXPORTED audit (D-54)."""
    runs = PipelineRunRepository(session)
    run = await runs.get(pipeline_run_id)
    if run is None:
        raise ExportNotFoundError(str(pipeline_run_id))
    if run.status != PipelineRunStatus.COMPLETED:
        raise ExportNotCompletedError(run.status.value)

    assets = AssetVersionRepository(session)
    approvals = ApprovalRepository(session)
    episode_id: uuid.UUID | None = None
    episode_number: int | None = None
    characters_payload: list[dict[str, str | None]] | None = None
    if run.character_ids or run.character_snapshot:
        characters_payload = await load_characters_for_export(run, session=session)
    if run.episode_id is not None:
        episode = await EpisodeRepository(session).get(run.episode_id)
        if episode is not None:
            episode_id = episode.id
            episode_number = episode.episode_number
    try:
        entries = await resolve_export_files(
            run,
            assets=assets,
            approvals=approvals,
            episode_number=episode_number,
        )
    except ExportAssetResolutionError as exc:
        raise RuntimeError(str(exc)) from exc

    result = await build_export_zip(
        pipeline_run_id=run.id,
        project_id=run.project_id,
        entries=entries,
        minio=minio,
        scene_count=run.scene_count,
        episode_id=episode_id,
        episode_number=episode_number,
        characters=characters_payload,
    )

    exported_iso = result.exported_at.isoformat().replace("+00:00", "Z")
    manifest_version = str(result.manifest_json.get("manifest_version", "1"))
    await AuditEventRepository(session).append(
        AuditEvent(
            project_id=run.project_id,
            pipeline_run_id=run.id,
            event_type=AuditEventType.BUNDLE_EXPORTED,
            payload={
                "pipeline_run_id": str(run.id),
                "project_id": str(run.project_id),
                "file_count": result.file_count,
                "manifest_hash": result.manifest_hash,
                "zip_size_bytes": len(result.zip_bytes),
                "exported_at": exported_iso,
                "manifest_version": manifest_version,
                "scene_count": run.scene_count,
                "episode_id": str(run.episode_id) if run.episode_id else None,
                "client_hint": "api",
            },
        )
    )
    await session.commit()
    return result
