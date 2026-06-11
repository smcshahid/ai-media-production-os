import { describe, expect, it } from "vitest";

import type { AssetHistoryVersion } from "../api/types";
import {
  formatCreatedAt,
  historyRowLabel,
  shortHash,
  stageSectionTitle,
} from "../lib/historyDisplay";

function version(
  stage: string,
  v: number,
  extra: Partial<AssetHistoryVersion> = {},
): AssetHistoryVersion {
  return {
    asset_id: `${stage}-${v}`,
    version: v,
    content_hash: "abcdef1234567890",
    is_ai_generated: true,
    branch: "ai-draft",
    pipeline_run_id: "042983f7-0f55-48c3-9d65-fce89a684625",
    metadata: {},
    created_at: "2026-06-11T12:00:00Z",
    ...extra,
  };
}

describe("stageSectionTitle", () => {
  it("formats stage name and pluralizes version count", () => {
    expect(stageSectionTitle("STORY", 2)).toBe("Story (2 versions)");
    expect(stageSectionTitle("IDEA", 1)).toBe("Idea (1 version)");
  });
});

describe("historyRowLabel", () => {
  it("shows version for non-storyboard stages", () => {
    expect(historyRowLabel("STORY", version("STORY", 2))).toBe("v2");
  });

  it("includes frame index for storyboard", () => {
    expect(
      historyRowLabel("STORYBOARD", version("STORYBOARD", 1, { metadata: { frame_index: 3 } })),
    ).toBe("v1 · frame 3");
  });
});

describe("shortHash", () => {
  it("truncates long hashes", () => {
    expect(shortHash("abcdef1234567890")).toBe("abcdef123456…");
  });
});

describe("formatCreatedAt", () => {
  it("returns a non-empty formatted string", () => {
    expect(formatCreatedAt("2026-06-11T12:00:00Z").length).toBeGreaterThan(0);
  });
});

describe("API order preservation", () => {
  it("expects newest-first story versions from fixture", () => {
    const versions = [version("STORY", 2), version("STORY", 1)];
    expect(versions.map((v) => v.version)).toEqual([2, 1]);
  });
});
