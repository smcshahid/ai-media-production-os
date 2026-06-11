"""Build lineage display chain and edge list (US-20 D-55)."""

from __future__ import annotations

import uuid

from aimpos_core.enums import AssetStage

from app.domain.export.resolver import ExportAssetResolutionError, resolve_export_files
from app.domain.lineage.types import LineageEdgeOut, LineageNode
from app.infrastructure.db.models.asset_version import AssetVersion
from app.infrastructure.db.models.pipeline_run import PipelineRun
from app.infrastructure.db.repositories.approval import ApprovalRepository
from app.infrastructure.db.repositories.asset_version import AssetVersionRepository


def _parents_for(child_id: uuid.UUID, edges: list[tuple[uuid.UUID, uuid.UUID]]) -> list[uuid.UUID]:
    return [parent for parent, child in edges if child == child_id]


def _node_from_asset(
    asset: AssetVersion,
    edges: list[tuple[uuid.UUID, uuid.UUID]],
    *,
    synthetic: bool = False,
) -> LineageNode:
    return LineageNode(
        asset_id=asset.id,
        stage=asset.stage.value,
        version=asset.version,
        content_hash=asset.content_hash,
        is_ai_generated=asset.is_ai_generated,
        branch=asset.branch,
        metadata=dict(asset.metadata_json or {}),
        parent_asset_ids=_parents_for(asset.id, edges) if not synthetic else [],
        synthetic=True if synthetic else None,
    )


async def build_lineage_view(
    run: PipelineRun,
    *,
    assets: AssetVersionRepository,
    approvals: ApprovalRepository,
    sql_edges: list[tuple[uuid.UUID, uuid.UUID]],
) -> tuple[list[LineageNode], list[LineageEdgeOut]]:
    """Return display-chain nodes and SQL-mirrored edges (SELECT-only inputs)."""
    edge_out = [
        LineageEdgeOut(parent_asset_id=parent, child_asset_id=child)
        for parent, child in sql_edges
    ]

    try:
        entries = await resolve_export_files(run, assets=assets, approvals=approvals)
    except ExportAssetResolutionError:
        return [], edge_out

    nodes: list[LineageNode] = []
    for entry in entries:
        is_idea = entry.asset.stage == AssetStage.IDEA
        nodes.append(
            _node_from_asset(entry.asset, sql_edges, synthetic=is_idea),
        )
    return nodes, edge_out
