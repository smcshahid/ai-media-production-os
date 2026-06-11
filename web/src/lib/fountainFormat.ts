/** Lightweight Fountain → HTML formatter (US-15 / T-15-02). */

const SCENE_HEADING_RE = /^(INT\.|EXT\.|INT\/EXT\.|I\/E\.)\s+.+$/;
const CHARACTER_CUE_RE = /^[A-Z0-9][A-Z0-9 .'\-()]{0,30}$/;
const TITLE_PAGE_PREFIXES = ["TITLE:", "CREDIT:", "AUTHOR:", "DRAFT DATE:", "CONTACT:"];

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function isTitlePageLine(line: string): boolean {
  const upper = line.trim().toUpperCase();
  return TITLE_PAGE_PREFIXES.some((prefix) => upper.startsWith(prefix));
}

function isParenthetical(line: string): boolean {
  const stripped = line.trim();
  return stripped.startsWith("(") && stripped.endsWith(")");
}

function isSceneHeading(line: string): boolean {
  return SCENE_HEADING_RE.test(line.trim());
}

function isCharacterCue(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed || isSceneHeading(trimmed) || isTitlePageLine(trimmed)) {
    return false;
  }
  return CHARACTER_CUE_RE.test(trimmed);
}

type Block =
  | { kind: "title-page"; text: string }
  | { kind: "scene"; text: string }
  | { kind: "action"; text: string }
  | { kind: "character"; text: string }
  | { kind: "parenthetical"; text: string }
  | { kind: "dialogue"; text: string };

function classifyLines(fountain: string): Block[] {
  const lines = fountain.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let mode: "action" | "dialogue" = "action";

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      mode = "action";
      continue;
    }

    if (isSceneHeading(line)) {
      blocks.push({ kind: "scene", text: line.trim() });
      mode = "action";
      continue;
    }
    if (isTitlePageLine(line)) {
      blocks.push({ kind: "title-page", text: line.trim() });
      mode = "action";
      continue;
    }
    if (isCharacterCue(line)) {
      blocks.push({ kind: "character", text: line.trim() });
      mode = "dialogue";
      continue;
    }
    if (mode === "dialogue" && isParenthetical(line)) {
      blocks.push({ kind: "parenthetical", text: line.trim() });
      continue;
    }
    if (mode === "dialogue") {
      blocks.push({ kind: "dialogue", text: line.trim() });
      continue;
    }
    blocks.push({ kind: "action", text: line.trim() });
  }

  return blocks;
}

function blockToHtml(block: Block): string {
  const text = escapeHtml(block.text);
  switch (block.kind) {
    case "scene":
      return `<h2 class="fountain-scene">${text}</h2>`;
    case "title-page":
      return `<p class="fountain-title-page">${text}</p>`;
    case "action":
      return `<p class="fountain-action">${text}</p>`;
    case "character":
      return `<p class="fountain-character">${text}</p>`;
    case "parenthetical":
      return `<p class="fountain-parenthetical">${text}</p>`;
    case "dialogue":
      return `<p class="fountain-dialogue">${text}</p>`;
    default:
      return `<p>${text}</p>`;
  }
}

/** Format Fountain plain text as safe HTML for preview rendering. */
export function formatFountainHtml(fountain: string): string {
  const trimmed = fountain.trim();
  if (!trimmed) {
    return "";
  }
  const blocks = classifyLines(trimmed);
  if (blocks.length === 0) {
    return `<pre class="fountain-raw">${escapeHtml(trimmed)}</pre>`;
  }
  return blocks.map(blockToHtml).join("\n");
}
