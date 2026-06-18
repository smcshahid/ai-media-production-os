"""Multi-scene pilot constants and Fountain helpers (Phase 4 / SCR-2026-002)."""

from __future__ import annotations

import re

MIN_SCENES = 1
MAX_SCENES = 3
DEFAULT_SCENE_INDEX = 1

SCENE_HEADING_RE = re.compile(
    r"^(?P<prefix>INT\.|EXT\.|INT/EXT\.|I/E\.)\s+(?P<location>.+?)(?:\s+-\s+(?P<time>.+))?$",
    re.MULTILINE,
)


def scene_index_from_metadata(metadata: dict | None) -> int:
    """Return 1-based scene index; legacy rows without metadata default to scene 1."""
    if not metadata:
        return DEFAULT_SCENE_INDEX
    raw = metadata.get("scene_index")
    if raw is None:
        return DEFAULT_SCENE_INDEX
    return int(raw)


def extract_fountain_scene(text: str, scene_index: int) -> str:
    """Extract one 1-based scene block from a multi-scene Fountain script."""
    if scene_index < 1:
        raise ValueError("scene_index must be >= 1")

    stripped = (text or "").strip()
    if not stripped:
        raise ValueError("script is empty")

    headings = list(SCENE_HEADING_RE.finditer(stripped))
    if not headings:
        raise ValueError("no scene headings found")

    if scene_index > len(headings):
        raise ValueError(
            f"scene_index {scene_index} exceeds scene count {len(headings)}"
        )

    start = headings[scene_index - 1].start()
    end = headings[scene_index].start() if scene_index < len(headings) else len(stripped)
    return stripped[start:end].strip()


def count_fountain_scenes(text: str) -> int:
    """Count Fountain scene headings in a script."""
    return len(list(SCENE_HEADING_RE.finditer((text or "").strip())))
