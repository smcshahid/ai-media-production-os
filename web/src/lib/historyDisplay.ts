/** Format asset history rows for stage-grouped display (US-23 D-58). */

import type { AssetHistoryVersion } from "../api/types";
import { shortHash } from "./lineageDisplay";

export function stageSectionTitle(stage: string, count: number): string {
  const label = stage.charAt(0) + stage.slice(1).toLowerCase();
  return `${label} (${count} version${count === 1 ? "" : "s"})`;
}

export function historyRowLabel(stage: string, version: AssetHistoryVersion): string {
  if (stage === "STORYBOARD") {
    const idx = version.metadata?.frame_index ?? "?";
    return `v${version.version} · frame ${idx}`;
  }
  return `v${version.version}`;
}

export function formatCreatedAt(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export { shortHash };
