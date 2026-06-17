import { useEffect, useMemo, useState } from "react";

import { ApiError, getAssetContent } from "../api/client";
import type { AssetHistoryVersion } from "../api/types";
import { diffLines } from "../lib/textDiff";

interface VersionDiffViewerProps {
  stage: "STORY" | "SCRIPT";
  versions: AssetHistoryVersion[];
}

export function VersionDiffViewer({ stage, versions }: VersionDiffViewerProps) {
  const sorted = useMemo(
    () => [...versions].sort((a, b) => a.version - b.version),
    [versions],
  );

  const [leftId, setLeftId] = useState<string>(() => sorted[0]?.asset_id ?? "");
  const [rightId, setRightId] = useState<string>(
    () => sorted[sorted.length - 1]?.asset_id ?? "",
  );
  const [leftText, setLeftText] = useState("");
  const [rightText, setRightText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sorted.length >= 2) {
      setLeftId(sorted[0].asset_id);
      setRightId(sorted[sorted.length - 1].asset_id);
    }
  }, [sorted]);

  useEffect(() => {
    if (!leftId || !rightId || leftId === rightId) {
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    Promise.all([getAssetContent(leftId), getAssetContent(rightId)])
      .then(([left, right]) => {
        if (active) {
          setLeftText(left);
          setRightText(right);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Failed to load versions for diff.");
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
  }, [leftId, rightId]);

  if (sorted.length < 2) {
    return (
      <p className="card__hint">
        At least two {stage.toLowerCase()} versions are required for comparison.
      </p>
    );
  }

  const diff = diffLines(leftText, rightText);

  return (
    <div className="version-diff">
      <div className="version-diff__pickers">
        <label>
          Left (older)
          <select value={leftId} onChange={(event) => setLeftId(event.target.value)}>
            {sorted.map((version) => (
              <option key={version.asset_id} value={version.asset_id}>
                v{version.version}
              </option>
            ))}
          </select>
        </label>
        <label>
          Right (newer)
          <select value={rightId} onChange={(event) => setRightId(event.target.value)}>
            {sorted.map((version) => (
              <option key={version.asset_id} value={version.asset_id}>
                v{version.version}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && <p className="card__hint">Loading versions…</p>}
      {error && (
        <p className="page__error" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && leftId === rightId && (
        <p className="card__hint">Select two different versions to compare.</p>
      )}

      {!loading && !error && leftId !== rightId && (
        <div className="version-diff__panes">
          <div className="version-diff__pane">
            <h4 className="version-diff__pane-title">Unified diff</h4>
            <pre className="version-diff__pre">
              {diff.map((line, index) => (
                <div
                  key={`${line.kind}-${index}`}
                  className={`version-diff__line version-diff__line--${line.kind}`}
                >
                  <span className="version-diff__marker">
                    {line.kind === "added" ? "+" : line.kind === "removed" ? "-" : " "}
                  </span>
                  {line.text || " "}
                </div>
              ))}
            </pre>
          </div>
          <div className="version-diff__pane">
            <h4 className="version-diff__pane-title">Side by side</h4>
            <div className="version-diff__side-by-side">
              <pre className="version-diff__pre version-diff__pre--column">{leftText}</pre>
              <pre className="version-diff__pre version-diff__pre--column">{rightText}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
