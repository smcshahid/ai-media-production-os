import type { AssetVersion } from "../api/types";

/** Latest ai-draft VIDEO asset at max version for a scene (US-18 / Phase 4). */
function sceneIndex(asset: AssetVersion): number {
  const raw = asset.metadata_json?.scene_index;
  if (typeof raw === "number") {
    return raw;
  }
  if (typeof raw === "string") {
    return parseInt(raw, 10);
  }
  return 1;
}

export function selectLatestAiDraftVideoAsset(
  assets: AssetVersion[],
  targetSceneIndex = 1,
): AssetVersion | null {
  const videos = assets.filter(
    (a) =>
      a.stage === "VIDEO" &&
      a.branch === "ai-draft" &&
      sceneIndex(a) === targetSceneIndex,
  );
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

export function narrationStatusLabel(asset: AssetVersion): string {
  if (asset.metadata_json?.has_narration === true) {
    const src = asset.metadata_json?.narration_source;
    if (src === "espeak") {
      return "Narrated (local TTS)";
    }
    if (src === "http_tts") {
      return "Narrated (HTTP TTS)";
    }
    return "Narrated";
  }
  return "Silent";
}
