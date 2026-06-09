"""Asset upload round-trip integration test (T-05-04).

Exercises the full path against the live compose stack:
``store_asset`` -> MinIO -> asset_versions row -> download -> hash verify, plus
the dedup policy (same bytes -> new version row, same blob key).

Skipped unless ``AIMPOS_RUN_INTEGRATION=1`` and the compose MinIO + PostgreSQL
are reachable (point settings at the dev-published ports). Not part of the
hermetic unit suite (testing-standards: integration is compose-based).
"""

from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.integration

_RUN = os.getenv("AIMPOS_RUN_INTEGRATION") == "1"


@pytest.mark.skipif(not _RUN, reason="needs compose MinIO+PostgreSQL; set AIMPOS_RUN_INTEGRATION=1")
@pytest.mark.asyncio
async def test_upload_round_trip_and_dedup() -> None:
    from aimpos_config import get_settings
    from aimpos_core.enums import AssetStage, ProjectStatus

    from app.domain.assets.content import compute_content_hash
    from app.domain.assets.service import store_asset
    from app.infrastructure.db.models.project import Project
    from app.infrastructure.db.repositories.asset_version import AssetVersionRepository
    from app.infrastructure.db.repositories.project import ProjectRepository
    from app.infrastructure.db.session import build_engine, build_sessionmaker
    from app.infrastructure.storage.minio_client import MinioClient

    settings = get_settings()
    engine = build_engine(settings.database_url)
    sessionmaker = build_sessionmaker(engine)
    minio = MinioClient.from_settings(settings)
    data = b"integration round-trip " + uuid.uuid4().bytes

    try:
        async with sessionmaker() as session:
            project = Project(name=f"it-{uuid.uuid4()}", status=ProjectStatus.ACTIVE)
            await ProjectRepository(session).add(project)
            versions = AssetVersionRepository(session)
            first = await store_asset(
                data=data,
                stage=AssetStage.IDEA,
                project_id=project.id,
                blobs=minio,
                versions=versions,
            )
            second = await store_asset(
                data=data,
                stage=AssetStage.IDEA,
                project_id=project.id,
                blobs=minio,
                versions=versions,
            )
            await session.commit()

        assert first.content_hash == compute_content_hash(data)
        assert (first.version, second.version) == (1, 2)
        assert first.minio_key == second.minio_key  # dedup

        downloaded = await minio.download_bytes(first.minio_key)
        assert downloaded == data
        assert compute_content_hash(downloaded) == first.content_hash
    finally:
        await engine.dispose()
