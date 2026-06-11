import { describe, expect, it } from "vitest";

import type { LineageNode } from "../api/types";
import { lineageNodeLabel, sortLineageNodes } from "../lib/lineageDisplay";

function node(stage: string, version = 1, extra: Partial<LineageNode> = {}): LineageNode {
  return {
    asset_id: `${stage}-${version}`,
    stage,
    version,
    content_hash: "abc123",
    is_ai_generated: stage !== "IDEA",
    branch: "main",
    metadata: {},
    parent_asset_ids: [],
    ...extra,
  };
}

describe("sortLineageNodes", () => {
  it("orders IDEA through VIDEO with storyboard frames by index", () => {
    const sorted = sortLineageNodes([
      node("VIDEO", 1),
      node("STORYBOARD", 1, { metadata: { frame_index: 3 } }),
      node("IDEA", 1, { synthetic: true }),
      node("SCRIPT", 1),
      node("STORYBOARD", 1, { metadata: { frame_index: 1 } }),
      node("STORY", 1),
      node("STORYBOARD", 1, { metadata: { frame_index: 2 } }),
    ]);
    expect(sorted.map((n) => n.stage)).toEqual([
      "IDEA",
      "STORY",
      "SCRIPT",
      "STORYBOARD",
      "STORYBOARD",
      "STORYBOARD",
      "VIDEO",
    ]);
    expect(
      sorted
        .filter((n) => n.stage === "STORYBOARD")
        .map((n) => Number(n.metadata.frame_index)),
    ).toEqual([1, 2, 3]);
  });
});

describe("lineageNodeLabel", () => {
  it("marks synthetic IDEA root", () => {
    expect(lineageNodeLabel(node("IDEA", 1, { synthetic: true }))).toBe(
      "Idea (presentation root)",
    );
  });

  it("includes frame index for storyboard", () => {
    expect(
      lineageNodeLabel(node("STORYBOARD", 2, { metadata: { frame_index: 4 } })),
    ).toBe("Storyboard frame 4 (v2)");
  });
});
