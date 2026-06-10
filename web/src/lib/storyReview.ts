import type { AssetVersion } from "../api/types";

/** Latest STORY asset by version number (human-edit or ai-draft). */
export function selectLatestStoryAsset(assets: AssetVersion[]): AssetVersion | null {
  const storyAssets = assets.filter((a) => a.stage === "STORY");
  if (storyAssets.length === 0) {
    return null;
  }
  return storyAssets.reduce((latest, row) => (row.version > latest.version ? row : latest));
}
