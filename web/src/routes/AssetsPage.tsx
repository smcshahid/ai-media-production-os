import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import { listAssets, listProjects, uploadAsset } from "../api/client";
import { ASSET_STAGES, type AssetStage, type AssetVersion, type Project } from "../api/types";

/**
 * Assets screen (US-05 frontend): upload a file to `POST /assets`, then show the
 * resulting versions (with content hash) from `GET /assets`. On failure the form
 * stays active and an error is shown.
 */
export function AssetsPage() {
  const [project, setProject] = useState<Project | null>(null);
  const [assets, setAssets] = useState<AssetVersion[]>([]);
  const [stage, setStage] = useState<AssetStage>("IDEA");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshAssets = useCallback(async (projectId: string) => {
    const rows = await listAssets(projectId);
    setAssets(rows);
  }, []);

  useEffect(() => {
    let active = true;
    listProjects()
      .then(async (projects) => {
        const first = projects[0] ?? null;
        if (!active) {
          return;
        }
        setProject(first);
        if (first) {
          await refreshAssets(first.id);
        }
      })
      .catch(() => {
        if (active) {
          setError("Failed to load assets.");
        }
      });
    return () => {
      active = false;
    };
  }, [refreshAssets]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!project) {
      setError("No project available to upload to.");
      return;
    }
    if (!file) {
      setError("Choose a file to upload.");
      return;
    }

    setError(null);
    setUploading(true);
    try {
      await uploadAsset(project.id, stage, file);
      await refreshAssets(project.id);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch {
      setError("Upload failed. Check the file and try again.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="page">
      <header className="page__header">
        <h1 className="page__title">Assets</h1>
        {project && <span className="page__subtitle">{project.name}</span>}
      </header>

      <form className="card" onSubmit={handleUpload}>
        <h2 className="card__title">Upload asset</h2>
        <div className="form-row">
          <label className="form-row__label" htmlFor="stage">
            Stage
          </label>
          <select
            id="stage"
            value={stage}
            onChange={(event) => setStage(event.target.value as AssetStage)}
          >
            {ASSET_STAGES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div className="form-row">
          <label className="form-row__label" htmlFor="file">
            File
          </label>
          <input
            id="file"
            ref={fileInputRef}
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </div>

        {error && (
          <p className="page__error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="button button--primary" disabled={uploading || !project}>
          {uploading ? "Uploading…" : "Upload"}
        </button>
      </form>

      <div className="card">
        <h2 className="card__title">Versions</h2>
        {assets.length === 0 ? (
          <p className="card__hint">No assets uploaded yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Stage</th>
                <th>Version</th>
                <th>Content hash</th>
                <th>Source</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id}>
                  <td>{asset.stage}</td>
                  <td>{asset.version}</td>
                  <td className="table__hash" title={asset.content_hash}>
                    {asset.content_hash.slice(0, 12)}…
                  </td>
                  <td>{asset.is_ai_generated ? "AI" : "Human"}</td>
                  <td>{new Date(asset.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
