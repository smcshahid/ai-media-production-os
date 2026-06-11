import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  getAssetContent,
  getAssetContentBlob,
  getAssetHistory,
} from "../api/client";
import type { AssetHistoryResponse, AssetHistoryVersion } from "../api/types";
import {
  formatCreatedAt,
  historyRowLabel,
  shortHash,
  stageSectionTitle,
} from "../lib/historyDisplay";

interface AssetHistoryViewerProps {
  projectId: string;
}

type PreviewState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "text"; content: string }
  | { kind: "image"; url: string }
  | { kind: "video"; url: string; filename: string }
  | { kind: "unavailable"; message: string }
  | { kind: "error"; message: string };

const TEXT_PREVIEW_MAX = 2000;

/**
 * Read-only stage-grouped asset history (US-23 D-58). D-57 data only — no flat list.
 */
export function AssetHistoryViewer({ projectId }: AssetHistoryViewerProps) {
  const [history, setHistory] = useState<AssetHistoryResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<AssetHistoryVersion | null>(null);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewState>({ kind: "idle" });

  useEffect(() => {
    let active = true;
    setLoading(true);
    setLoadError(null);
    setHistory(null);
    setSelected(null);
    setSelectedStage(null);
    setPreview({ kind: "idle" });

    getAssetHistory(projectId)
      .then((data) => {
        if (active) {
          setHistory(data);
        }
      })
      .catch((err) => {
        if (active) {
          if (err instanceof ApiError && err.status === 404) {
            setLoadError("Project not found.");
          } else {
            setLoadError(
              err instanceof ApiError ? err.message : "Failed to load asset history.",
            );
          }
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
  }, [projectId]);

  useEffect(() => {
    return () => {
      if (preview.kind === "image" || preview.kind === "video") {
        URL.revokeObjectURL(preview.url);
      }
    };
  }, [preview]);

  const handleSelect = useCallback((stage: string, version: AssetHistoryVersion) => {
    setSelected(version);
    setSelectedStage(stage);
    setPreview({ kind: "idle" });
  }, []);

  const handlePreview = useCallback(async () => {
    if (!selected || !selectedStage) {
      return;
    }

    if (selectedStage === "IDEA") {
      setPreview({
        kind: "unavailable",
        message: "Content preview is not available for IDEA assets.",
      });
      return;
    }

    setPreview({ kind: "loading" });

    try {
      if (selectedStage === "STORY" || selectedStage === "SCRIPT") {
        const text = await getAssetContent(selected.asset_id);
        setPreview({ kind: "text", content: text });
        return;
      }

      const blob = await getAssetContentBlob(selected.asset_id);
      const url = URL.createObjectURL(blob);

      if (selectedStage === "STORYBOARD") {
        setPreview({ kind: "image", url });
        return;
      }

      if (selectedStage === "VIDEO") {
        setPreview({
          kind: "video",
          url,
          filename: `video-v${selected.version}.mp4`,
        });
        return;
      }

      URL.revokeObjectURL(url);
      setPreview({ kind: "unavailable", message: "Preview is not available for this stage." });
    } catch (err) {
      setPreview({
        kind: "error",
        message: err instanceof ApiError ? err.message : "Failed to load preview.",
      });
    }
  }, [selected, selectedStage]);

  if (loading) {
    return <p className="card__hint">Loading asset history…</p>;
  }

  if (loadError) {
    return (
      <p className="page__error" role="alert">
        {loadError}
      </p>
    );
  }

  if (!history || history.stages.length === 0) {
    return <p className="card__hint">No asset versions recorded for this project.</p>;
  }

  const totalVersions = history.stages.reduce((sum, s) => sum + s.versions.length, 0);

  return (
    <div className="history">
      <p className="card__hint">
        {totalVersions} version{totalVersions === 1 ? "" : "s"} across {history.stages.length}{" "}
        stage{history.stages.length === 1 ? "" : "s"}. Click a row for metadata.
      </p>

      {history.stages.map((stageGroup) => (
        <section key={stageGroup.stage} className="history__section">
          <h3 className="history__section-title">
            {stageSectionTitle(stageGroup.stage, stageGroup.versions.length)}
          </h3>
          <ol className="history__list">
            {stageGroup.versions.map((version) => {
              const isSelected = selected?.asset_id === version.asset_id;
              return (
                <li
                  key={version.asset_id}
                  className={`history__row${isSelected ? " history__row--selected" : ""}`}
                >
                  <button
                    type="button"
                    className="history__row-button"
                    onClick={() => handleSelect(stageGroup.stage, version)}
                  >
                    <span className="history__label">
                      {historyRowLabel(stageGroup.stage, version)}
                    </span>
                    <span className="badge badge--review">{version.branch}</span>
                    {version.is_ai_generated && (
                      <span className="badge badge--review">AI</span>
                    )}
                    <span className="history__hash">{shortHash(version.content_hash)}</span>
                  </button>
                </li>
              );
            })}
          </ol>
        </section>
      ))}

      {selected && selectedStage && (
        <div className="history__panel" aria-live="polite">
          <h3 className="history__panel-title">Version metadata</h3>
          <dl className="history__meta">
            <div>
              <dt>Stage</dt>
              <dd>{selectedStage}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{selected.version}</dd>
            </div>
            <div>
              <dt>Asset ID</dt>
              <dd className="history__mono">{selected.asset_id}</dd>
            </div>
            <div>
              <dt>Content hash</dt>
              <dd className="history__mono">{selected.content_hash}</dd>
            </div>
            <div>
              <dt>Branch</dt>
              <dd>{selected.branch}</dd>
            </div>
            <div>
              <dt>AI generated</dt>
              <dd>{selected.is_ai_generated ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{formatCreatedAt(selected.created_at)}</dd>
            </div>
            <div>
              <dt>Pipeline run</dt>
              <dd className="history__mono">{selected.pipeline_run_id ?? "—"}</dd>
            </div>
            {selectedStage === "STORYBOARD" && selected.metadata?.frame_index != null && (
              <div>
                <dt>Frame index</dt>
                <dd>{String(selected.metadata.frame_index)}</dd>
              </div>
            )}
          </dl>

          <div className="history__preview-actions">
            <button type="button" className="history__preview-button" onClick={handlePreview}>
              {selectedStage === "VIDEO" ? "Download" : "Preview"}
            </button>
          </div>

          {preview.kind === "loading" && <p className="card__hint">Loading preview…</p>}
          {preview.kind === "unavailable" && (
            <p className="card__hint" role="note">
              {preview.message}
            </p>
          )}
          {preview.kind === "error" && (
            <p className="page__error" role="alert">
              {preview.message}
            </p>
          )}
          {preview.kind === "text" && (
            <pre className="history__preview-text">
              {preview.content.length > TEXT_PREVIEW_MAX
                ? `${preview.content.slice(0, TEXT_PREVIEW_MAX)}…`
                : preview.content}
            </pre>
          )}
          {preview.kind === "image" && (
            <img
              className="history__preview-image"
              src={preview.url}
              alt={`Storyboard frame preview v${selected.version}`}
            />
          )}
          {preview.kind === "video" && (
            <a className="history__download-link" href={preview.url} download={preview.filename}>
              Download video (v{selected.version})
            </a>
          )}
        </div>
      )}
    </div>
  );
}
