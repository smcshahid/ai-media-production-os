import type { AssetVersion } from "../api/types";

/** Latest STORY asset by version number (human-edit or ai-draft). */
export function selectLatestStoryAsset(assets: AssetVersion[]): AssetVersion | null {
  const storyAssets = assets.filter((a) => a.stage === "STORY");
  if (storyAssets.length === 0) {
    return null;
  }
  return storyAssets.reduce((latest, row) => (row.version > latest.version ? row : latest));
}

/** Latest ai-draft STORY asset (D-38 — after regenerate, show new model output). */
export function selectLatestAiDraftStoryAsset(assets: AssetVersion[]): AssetVersion | null {
  const drafts = assets.filter((a) => a.stage === "STORY" && a.branch === "ai-draft");
  if (drafts.length === 0) {
    return null;
  }
  return drafts.reduce((latest, row) => (row.version > latest.version ? row : latest));
}
