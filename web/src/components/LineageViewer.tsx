import { useCallback, useEffect, useState } from "react";

import { ApiError, getLineage } from "../api/client";
import type { LineageNode, LineageResponse } from "../api/types";
import { lineageNodeLabel, shortHash, sortLineageNodes } from "../lib/lineageDisplay";

interface LineageViewerProps {
  runId: string;
}

/**
 * Read-only lineage list/tree (US-20 D-56). HTML/CSS only — no graph libraries.
 */
export function LineageViewer({ runId }: LineageViewerProps) {
  const [lineage, setLineage] = useState<LineageResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<LineageNode | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError(null);
    getLineage(runId)
      .then((data) => {
        if (active) {
          setLineage(data);
          setSelected(null);
        }
      })
      .catch((err) => {
        if (active) {
          setLoadError(err instanceof ApiError ? err.message : "Failed to load lineage.");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [runId]);

  const nodes = sortLineageNodes(lineage?.nodes ?? []);

  const handleSelect = useCallback((node: LineageNode) => {
    setSelected(node);
  }, []);

  if (loading) {
    return <p className="card__hint">Loading lineage…</p>;
  }

  if (loadError) {
    return (
      <p className="page__error" role="alert">
        {loadError}
      </p>
    );
  }

  if (!lineage || nodes.length === 0) {
    return <p className="card__hint">No lineage nodes available for this run.</p>;
  }

  return (
    <div className="lineage">
      <p className="card__hint">
        {lineage.edges.length} provenance edge{lineage.edges.length === 1 ? "" : "s"} from
        PostgreSQL. Click a row for metadata.
      </p>

      <ol className="lineage__tree">
        {nodes.map((node) => {
          const depth =
            node.stage === "IDEA"
              ? 0
              : node.stage === "STORY"
                ? 1
                : node.stage === "SCRIPT"
                  ? 2
                  : node.stage === "STORYBOARD"
                    ? 3
                    : 4;
          const isSelected = selected?.asset_id === node.asset_id;
          return (
            <li
              key={node.asset_id}
              className={`lineage__row${isSelected ? " lineage__row--selected" : ""}`}
              style={{ paddingLeft: `${12 + depth * 16}px` }}
            >
              <button
                type="button"
                className="lineage__row-button"
                onClick={() => handleSelect(node)}
              >
                <span className="lineage__label">{lineageNodeLabel(node)}</span>
                {node.synthetic && (
                  <span
                    className="badge badge--review lineage__synthetic"
                    title="Not stored as a lineage edge; shown for context only."
                  >
                    synthetic
                  </span>
                )}
                <span className="lineage__hash">{shortHash(node.content_hash)}</span>
              </button>
            </li>
          );
        })}
      </ol>

      {selected && (
        <div className="lineage__panel" aria-live="polite">
          <h3 className="lineage__panel-title">Node metadata</h3>
          <dl className="lineage__meta">
            <div>
              <dt>Stage</dt>
              <dd>{selected.stage}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{selected.version}</dd>
            </div>
            <div>
              <dt>Content hash</dt>
              <dd className="lineage__mono">{selected.content_hash}</dd>
            </div>
            <div>
              <dt>Branch</dt>
              <dd>{selected.branch}</dd>
            </div>
            <div>
              <dt>AI generated</dt>
              <dd>{selected.is_ai_generated ? "Yes" : "No"}</dd>
            </div>
            {selected.stage === "STORYBOARD" && selected.metadata?.frame_index != null && (
              <div>
                <dt>Frame index</dt>
                <dd>{String(selected.metadata.frame_index)}</dd>
              </div>
            )}
            {selected.synthetic && (
              <div>
                <dt>Presentation root</dt>
                <dd>Not stored as a lineage edge (C-01).</dd>
              </div>
            )}
            {selected.parent_asset_ids.length > 0 && (
              <div>
                <dt>Parent asset IDs</dt>
                <dd className="lineage__mono">{selected.parent_asset_ids.join(", ")}</dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}
