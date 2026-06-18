"""Fountain validation for US-14 (D-40 superseded by D-74 multi-scene pilot)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aimpos_core.scene import MAX_SCENES, MIN_SCENES, SCENE_HEADING_RE

CHARACTER_CUE_RE = re.compile(r"^[A-Z0-9][A-Z0-9 .'\-()]{0,30}$")

TITLE_PAGE_PREFIXES = ("TITLE:", "CREDIT:", "AUTHOR:", "DRAFT DATE:", "CONTACT:")


@dataclass(frozen=True, slots=True)
class FountainValidationResult:
    ok: bool
    errors: tuple[str, ...]
    scene_heading_count: int
    scene_count: int
    dialogue_count: int


class FountainValidationError(ValueError):
    """Raised when Fountain output fails validation."""


def _is_title_page_line(line: str) -> bool:
    upper = line.strip().upper()
    return any(upper.startswith(prefix) for prefix in TITLE_PAGE_PREFIXES)


def _is_parenthetical(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("(") and stripped.endswith(")")


def count_dialogue_blocks(lines: list[str]) -> int:
    """Count character cues that have at least one following dialogue line."""
    count = 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if (
            not line
            or SCENE_HEADING_RE.match(line)
            or _is_title_page_line(line)
            or not CHARACTER_CUE_RE.match(line)
        ):
            i += 1
            continue

        j = i + 1
        if j < len(lines) and _is_parenthetical(lines[j].strip()):
            j += 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines):
            dialogue = lines[j].strip()
            if (
                dialogue
                and not SCENE_HEADING_RE.match(dialogue)
                and not CHARACTER_CUE_RE.match(dialogue)
                and not _is_title_page_line(dialogue)
            ):
                count += 1
        i += 1
    return count


def validate_fountain(
    text: str, *, expected_scene_count: int | None = None
) -> FountainValidationResult:
    """Validate Fountain output (1–3 scenes for pilot; D-74)."""
    errors: list[str] = []
    stripped = (text or "").strip()

    if not stripped:
        return FountainValidationResult(
            ok=False,
            errors=("script is empty",),
            scene_heading_count=0,
            scene_count=0,
            dialogue_count=0,
        )

    headings = list(SCENE_HEADING_RE.finditer(stripped))
    scene_heading_count = len(headings)
    scene_count = scene_heading_count
    lines = stripped.splitlines()
    dialogue_count = count_dialogue_blocks(lines)

    if scene_heading_count == 0:
        errors.append("scene_heading_count == 0")
    if scene_count < MIN_SCENES or scene_count > MAX_SCENES:
        errors.append(
            f"scene_count out of range {MIN_SCENES}-{MAX_SCENES} (found {scene_count})"
        )
    elif expected_scene_count is not None and scene_count != expected_scene_count:
        errors.append(
            f"scene_count != {expected_scene_count} (found {scene_count})"
        )
    if dialogue_count == 0:
        errors.append("dialogue_count == 0")

    return FountainValidationResult(
        ok=len(errors) == 0,
        errors=tuple(errors),
        scene_heading_count=scene_heading_count,
        scene_count=scene_count,
        dialogue_count=dialogue_count,
    )


def require_valid_fountain(
    text: str, *, expected_scene_count: int | None = None
) -> FountainValidationResult:
    """Validate and raise ``FountainValidationError`` on failure."""
    result = validate_fountain(text, expected_scene_count=expected_scene_count)
    if not result.ok:
        raise FountainValidationError("; ".join(result.errors))
    return result
