import { describe, expect, it } from "vitest";

import { selectLatestAiDraftVideoAsset, narrationStatusLabel, videoSourceLabel } from "../lib/videoReview";
import type { AssetVersion } from "../api/types";

function asset(partial: Partial<AssetVersion> & Pick<AssetVersion, "id" | "version" | "stage">): AssetVersion {
  return {
    project_id: "p1",
    content_hash: "abc",
    minio_key: "k",
    is_ai_generated: true,
    branch: "ai-draft",
    created_at: "2026-01-01T00:00:00Z",
    ...partial,
  };
}

describe("videoReview", () => {
  it("selects the highest VIDEO ai-draft version", () => {
    const assets: AssetVersion[] = [
      asset({ id: "v1", stage: "VIDEO", version: 1 }),
      asset({ id: "v2", stage: "VIDEO", version: 2 }),
      asset({ id: "s1", stage: "STORYBOARD", version: 1 }),
    ];
    expect(selectLatestAiDraftVideoAsset(assets)?.id).toBe("v2");
  });

  it("labels slideshow and comfyui sources", () => {
    expect(
      videoSourceLabel(
        asset({ id: "v1", stage: "VIDEO", version: 1, metadata_json: { source: "slideshow" } }),
      ),
    ).toBe("Slideshow (storyboard frames)");
    expect(
      videoSourceLabel(
        asset({ id: "v2", stage: "VIDEO", version: 1, metadata_json: { source: "comfyui_i2v" } }),
      ),
    ).toBe("ComfyUI image-to-video");
  });

  it("labels narration status", () => {
    expect(
      narrationStatusLabel(
        asset({
          id: "v1",
          stage: "VIDEO",
          version: 1,
          metadata_json: { has_narration: true, narration_source: "espeak" },
        }),
      ),
    ).toBe("Narrated (local TTS)");
    expect(
      narrationStatusLabel(
        asset({ id: "v2", stage: "VIDEO", version: 1, metadata_json: {} }),
      ),
    ).toBe("Silent");
  });
});
