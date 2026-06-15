import type { AssetVersion } from "../api/types";

/** Latest ai-draft VIDEO asset at max version (US-18). */
export function selectLatestAiDraftVideoAsset(assets: AssetVersion[]): AssetVersion | null {
  const videos = assets.filter((a) => a.stage === "VIDEO" && a.branch === "ai-draft");
  if (videos.length === 0) {
    return null;
  }
  return videos.reduce((latest, row) => (row.version > latest.version ? row : latest));
}

export function videoSourceLabel(asset: AssetVersion): string {
  const source = asset.metadata_json?.source;
  if (source === "comfyui_i2v") {
    return "ComfyUI image-to-video";
  }
  if (source === "slideshow") {
    return "Slideshow (storyboard frames)";
  }
  return typeof source === "string" ? source : "Unknown";
}
