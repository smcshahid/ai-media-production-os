"""T-04-01 acceptance: models import cleanly and the schema is complete.

Verifies the T-04-01 acceptance criteria without a live PostgreSQL:
  * model files exist for all 6 tables and import without circular errors;
  * ``asset_versions`` carries the AC-mandated columns;
  * foreign keys/indexes exist for ``project_id`` and ``pipeline_run_id``;
  * the metadata builds (``create_all`` on in-memory SQLite).
"""

from __future__ import annotations

from sqlalchemy import create_engine

from app.infrastructure.db.models import (
    Approval,
    AssetVersion,
    AuditEvent,
    Base,
    Character,
    Episode,
    LineageEdge,
    PipelineRun,
    Project,
)

EXPECTED_TABLES = {
    "projects",
    "episodes",
    "characters",
    "pipeline_runs",
    "asset_versions",
    "approvals",
    "audit_events",
    "lineage_edges",
}


def test_all_core_tables_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_models_are_importable() -> None:
    for model in (
        Project,
        Episode,
        Character,
        PipelineRun,
        AssetVersion,
        Approval,
        AuditEvent,
        LineageEdge,
    ):
        assert model.__tablename__ in EXPECTED_TABLES


def test_asset_versions_required_columns() -> None:
    columns = set(AssetVersion.__table__.columns.keys())
    required = {"stage", "version", "minio_key", "content_hash", "is_ai_generated", "branch"}
    assert required.issubset(columns)


def test_foreign_keys_and_indexes_present() -> None:
    fk_columns = {fk.parent.name for fk in AssetVersion.__table__.foreign_keys}
    assert {"project_id", "pipeline_run_id"}.issubset(fk_columns)

    indexed = {col.name for col in AssetVersion.__table__.columns if col.index}
    assert {"project_id", "pipeline_run_id"}.issubset(indexed)

    run_fks = {fk.parent.name for fk in PipelineRun.__table__.foreign_keys}
    assert "episode_id" in run_fks


def test_metadata_creates_on_sqlite() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    engine.dispose()
