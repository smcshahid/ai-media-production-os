"""Repository for the AssetVersion aggregate root."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from aimpos_core.enums import AssetStage
from aimpos_core.scene import scene_index_from_metadata
from sqlalchemy import func, select

from app.domain.assets.service import StoredAsset
from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.repositories.base import SQLAlchemyRepository


class AssetVersionRepository(SQLAlchemyRepository[AssetVersion]):
    model = AssetVersion

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
    ) -> StoredAsset:
        """Persist a new asset version (port impl for ``store_asset``).

        Maps the ORM row to a framework-free ``StoredAsset`` so the domain never
        sees SQLAlchemy. Flushes (not commits) — the caller owns the transaction.
        """
        row = AssetVersion(
            project_id=project_id,
            stage=stage,
            version=version,
            minio_key=minio_key,
            content_hash=content_hash,
            is_ai_generated=is_ai_generated,
            branch=branch,
            metadata_json=metadata_json,
        )
        await self.add(row)
        return StoredAsset(
            id=row.id,
            project_id=row.project_id,
            stage=row.stage,
            version=row.version,
            minio_key=row.minio_key,
            content_hash=row.content_hash,
            is_ai_generated=row.is_ai_generated,
            branch=row.branch,
            metadata_json=row.metadata_json,
        )

    async def next_version(self, project_id: uuid.UUID, stage: AssetStage) -> int:
        """Return the next version number for a ``(project, stage)`` chain.

        Used by ``store_asset`` (US-05 / T-05-03) to increment versions.
        """

        result = await self.session.execute(
            select(func.max(AssetVersion.version)).where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == stage,
            )
        )
        current = result.scalar_one_or_none()
        return (current or 0) + 1

    async def list_for_project(self, project_id: uuid.UUID) -> Sequence[AssetVersion]:
        result = await self.session.execute(
            select(AssetVersion)
            .where(AssetVersion.project_id == project_id)
            .order_by(AssetVersion.created_at.desc())
        )
        return result.scalars().all()

    async def max_version(self, project_id: uuid.UUID, stage: AssetStage) -> int:
        result = await self.session.execute(
            select(func.max(AssetVersion.version)).where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == stage,
            )
        )
        return int(result.scalar_one_or_none() or 0)

    async def latest_for_run(
        self,
        project_id: uuid.UUID,
        stage: AssetStage,
        pipeline_run_id: uuid.UUID,
    ) -> AssetVersion | None:
        """Return latest asset version scoped to a pipeline run (Phase 6 episode export)."""
        result = await self.session.execute(
            select(AssetVersion)
            .where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == stage,
                AssetVersion.pipeline_run_id == pipeline_run_id,
            )
            .order_by(AssetVersion.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_at_version(
        self, project_id: uuid.UUID, stage: AssetStage, version: int
    ) -> AssetVersion | None:
        result = await self.session.execute(
            select(AssetVersion)
            .where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == stage,
                AssetVersion.version == version,
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_storyboard_batch(
        self, project_id: uuid.UUID, version: int
    ) -> Sequence[AssetVersion]:
        result = await self.session.execute(
            select(AssetVersion)
            .where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == AssetStage.STORYBOARD,
                AssetVersion.version == version,
            )
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda row: int((row.metadata_json or {}).get("frame_index", 0)))
        return rows

    async def list_storyboard_batch_for_scene(
        self, project_id: uuid.UUID, scene_index: int
    ) -> Sequence[AssetVersion]:
        """Return latest storyboard batch rows for a scene (Phase 4)."""
        result = await self.session.execute(
            select(AssetVersion).where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == AssetStage.STORYBOARD,
            )
        )
        rows = [
            row
            for row in result.scalars().all()
            if scene_index_from_metadata(row.metadata_json) == scene_index
        ]
        if not rows:
            return []
        max_version = max(row.version for row in rows)
        batch = [row for row in rows if row.version == max_version]
        batch.sort(key=lambda row: int((row.metadata_json or {}).get("frame_index", 0)))
        return batch

    async def latest_video_for_scene(
        self,
        project_id: uuid.UUID,
        scene_index: int,
        *,
        pipeline_run_id: uuid.UUID | None = None,
    ) -> AssetVersion | None:
        result = await self.session.execute(
            select(AssetVersion).where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == AssetStage.VIDEO,
            )
        )
        rows = [
            row
            for row in result.scalars().all()
            if scene_index_from_metadata(row.metadata_json) == scene_index
        ]
        if pipeline_run_id is not None:
            scoped = [row for row in rows if row.pipeline_run_id == pipeline_run_id]
            if scoped:
                rows = scoped
            else:
                legacy = [row for row in rows if row.pipeline_run_id is None]
                if legacy:
                    rows = legacy
        if not rows:
            return None
        max_version = max(row.version for row in rows)
        for row in rows:
            if row.version == max_version:
                return row
        return None

    async def latest_narration_for_scene(
        self,
        project_id: uuid.UUID,
        scene_index: int,
        *,
        pipeline_run_id: uuid.UUID | None = None,
    ) -> AssetVersion | None:
        result = await self.session.execute(
            select(AssetVersion).where(
                AssetVersion.project_id == project_id,
                AssetVersion.stage == AssetStage.NARRATION,
            )
        )
        rows = [
            row
            for row in result.scalars().all()
            if scene_index_from_metadata(row.metadata_json) == scene_index
        ]
        if pipeline_run_id is not None:
            scoped = [row for row in rows if row.pipeline_run_id == pipeline_run_id]
            if scoped:
                rows = scoped
            else:
                legacy = [row for row in rows if row.pipeline_run_id is None]
                if legacy:
                    rows = legacy
        if not rows:
            return None
        max_version = max(row.version for row in rows)
        for row in rows:
            if row.version == max_version:
                return row
        return None

    async def list_history_for_project(
        self,
        project_id: uuid.UUID,
        *,
        stage: AssetStage | None = None,
        pipeline_run_id: uuid.UUID | None = None,
    ) -> Sequence[AssetVersion]:
        """Read-only history query for US-22 (SELECT only — no writes)."""
        query = select(AssetVersion).where(AssetVersion.project_id == project_id)
        if stage is not None:
            query = query.where(AssetVersion.stage == stage)
        if pipeline_run_id is not None:
            from sqlalchemy import or_

            query = query.where(
                or_(
                    AssetVersion.pipeline_run_id == pipeline_run_id,
                    AssetVersion.stage == AssetStage.IDEA,
                )
            )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_for_project(
        self,
        project_id: uuid.UUID,
        *,
        stage: AssetStage | None = None,
        pipeline_run_id: uuid.UUID | None = None,
    ) -> int:
        """Count rows matching history filters (verify / tests)."""
        from sqlalchemy import func, or_

        query = select(func.count()).select_from(AssetVersion).where(
            AssetVersion.project_id == project_id
        )
        if stage is not None:
            query = query.where(AssetVersion.stage == stage)
        if pipeline_run_id is not None:
            query = query.where(
                or_(
                    AssetVersion.pipeline_run_id == pipeline_run_id,
                    AssetVersion.stage == AssetStage.IDEA,
                )
            )
        result = await self.session.execute(query)
        return int(result.scalar_one())
