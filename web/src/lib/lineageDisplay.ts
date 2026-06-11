/** Format lineage nodes for list/tree display (US-20 D-56). */

import type { LineageNode } from "../api/types";

const STAGE_ORDER: Record<string, number> = {
  IDEA: 0,
  STORY: 1,
  SCRIPT: 2,
  STORYBOARD: 3,
  VIDEO: 4,
};

/** Stable sort: stage order, then frame_index for storyboard, then version. */
export function sortLineageNodes(nodes: LineageNode[]): LineageNode[] {
  return [...nodes].sort((a, b) => {
    const stageDiff = (STAGE_ORDER[a.stage] ?? 99) - (STAGE_ORDER[b.stage] ?? 99);
    if (stageDiff !== 0) {
      return stageDiff;
    }
    if (a.stage === "STORYBOARD" && b.stage === "STORYBOARD") {
      const ai = Number(a.metadata?.frame_index ?? 0);
      const bi = Number(b.metadata?.frame_index ?? 0);
      return ai - bi;
    }
    return a.version - b.version;
  });
}

export function lineageNodeLabel(node: LineageNode): string {
  if (node.stage === "STORYBOARD") {
    const idx = node.metadata?.frame_index ?? "?";
    return `Storyboard frame ${idx} (v${node.version})`;
  }
  if (node.stage === "IDEA" && node.synthetic) {
    return "Idea (presentation root)";
  }
  return `${node.stage} (v${node.version})`;
}

export function shortHash(hash: string): string {
  return hash.length > 12 ? `${hash.slice(0, 12)}…` : hash;
}
