"""Fountain narration text extraction (Phase 5 / SCR-2026-003)."""

from __future__ import annotations

import re

from aimpos_core.scene import SCENE_HEADING_RE, extract_fountain_scene

# Character cue: mostly uppercase name line (Fountain convention).
_CHARACTER_CUE_RE = re.compile(
    r"^[A-Z][A-Z0-9 \.'\"()\-]{0,60}$"
)


def extract_narration_text_from_fountain(scene_text: str) -> str:
    """Collect dialogue lines from one Fountain scene block for TTS."""
    stripped = (scene_text or "").strip()
    if not stripped:
        return ""

    dialogue_parts: list[str] = []
    lines = stripped.splitlines()
    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        line = raw.strip()
        idx += 1
        if not line or SCENE_HEADING_RE.match(line):
            continue
        if line.startswith("(") and line.endswith(")"):
            continue
        if _CHARACTER_CUE_RE.match(line) and not line.endswith("TO:"):
            while idx < len(lines):
                next_line = lines[idx].strip()
                if not next_line:
                    idx += 1
                    break
                if _CHARACTER_CUE_RE.match(next_line) or SCENE_HEADING_RE.match(next_line):
                    break
                if next_line.startswith("(") and next_line.endswith(")"):
                    idx += 1
                    continue
                dialogue_parts.append(next_line)
                idx += 1
            continue

    text = " ".join(dialogue_parts).strip()
    if text:
        return text[:2000]

    # Fallback: narrate scene body minus headings (action/description).
    body = SCENE_HEADING_RE.sub("", stripped)
    body = re.sub(r"\([^)]+\)", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:800]


def narration_text_for_scene(script_fountain: str, scene_index: int) -> str:
    """Extract TTS input for a 1-based scene index."""
    scene_block = extract_fountain_scene(script_fountain, scene_index)
    return extract_narration_text_from_fountain(scene_block)
