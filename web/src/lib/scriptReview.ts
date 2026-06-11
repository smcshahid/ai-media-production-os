import type { AssetVersion } from "../api/types";

/** Latest ai-draft SCRIPT asset (D-38 / D-39 — after regenerate, show new model output). */
export function selectLatestAiDraftScriptAsset(assets: AssetVersion[]): AssetVersion | null {
  const drafts = assets.filter((a) => a.stage === "SCRIPT" && a.branch === "ai-draft");
  if (drafts.length === 0) {
    return null;
  }
  return drafts.reduce((latest, row) => (row.version > latest.version ? row : latest));
}
