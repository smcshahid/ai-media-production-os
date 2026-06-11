"""US-16 shot plan and PNG validation (D-45)."""

from __future__ import annotations

import pytest

from app.agents.cinematography.constants import STORYBOARD_FRAME_COUNT
from app.agents.cinematography.validate import validate_shot_plan, validate_storyboard_frame


def _four_shots() -> list[dict]:
    return [
        {"frame_index": i, "shot_label": f"S{i}", "prompt": f"prompt {i}"}
        for i in range(1, STORYBOARD_FRAME_COUNT + 1)
    ]


def test_validate_shot_plan_accepts_four_frames() -> None:
    validate_shot_plan(_four_shots())  # no raise


def test_validate_shot_plan_rejects_wrong_count() -> None:
    with pytest.raises(ValueError, match="exactly 4"):
        validate_shot_plan(_four_shots()[:3])


def test_validate_shot_plan_rejects_duplicate_index() -> None:
    shots = _four_shots()
    shots[3]["frame_index"] = 2
    with pytest.raises(ValueError, match="frame_index"):
        validate_shot_plan(shots)


def test_validate_storyboard_frame_accepts_png_magic() -> None:
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    validate_storyboard_frame(png)


def test_validate_storyboard_frame_rejects_non_png() -> None:
    with pytest.raises(ValueError, match="magic"):
        validate_storyboard_frame(b"not-a-png-file-content" + b"\x00" * 32)
