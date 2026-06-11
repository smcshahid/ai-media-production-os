"""Shot plan and PNG validation gates (US-16 / D-44 / D-45)."""

from __future__ import annotations

from app.agents.cinematography.constants import STORYBOARD_FRAME_COUNT
from app.agents.cinematography.state import ShotPlan

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def validate_shot_plan(shots: list[ShotPlan]) -> None:
    """Fail when plan does not satisfy D-45 (exactly 4 unique indexed shots)."""
    if len(shots) != STORYBOARD_FRAME_COUNT:
        raise ValueError(
            f"expected exactly {STORYBOARD_FRAME_COUNT} shots, found {len(shots)}"
        )
    indexes = sorted(int(s["frame_index"]) for s in shots)
    expected = list(range(1, STORYBOARD_FRAME_COUNT + 1))
    if indexes != expected:
        raise ValueError(f"frame_index must be 1..{STORYBOARD_FRAME_COUNT}, got {indexes}")
    for shot in shots:
        prompt = (shot.get("prompt") or "").strip()
        if not prompt:
            raise ValueError(f"empty prompt for frame_index={shot.get('frame_index')}")


def validate_storyboard_frame(png_bytes: bytes) -> None:
    """Fail when PNG bytes are invalid (D-44 pre-store check)."""
    if not png_bytes or len(png_bytes) < 32:
        raise ValueError("png frame is empty or too small")
    if png_bytes[:8] != PNG_MAGIC:
        raise ValueError("png frame missing PNG magic bytes")
