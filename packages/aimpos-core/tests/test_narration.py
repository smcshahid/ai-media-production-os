"""Tests for Fountain narration text extraction."""

from aimpos_core.narration import (
    extract_narration_text_from_fountain,
    narration_text_for_scene,
)


def test_extract_dialogue_from_fountain_scene() -> None:
    scene = """INT. LAB - NIGHT

DR. REED
The coral sings at midnight.

MAYA
We should broadcast this."""
    text = extract_narration_text_from_fountain(scene)
    assert "coral sings" in text
    assert "broadcast" in text


def test_narration_text_for_scene_index() -> None:
    script = """INT. ONE - DAY

ALICE
Scene one line.

EXT. TWO - NIGHT

BOB
Scene two line."""
    one = narration_text_for_scene(script, 1)
    two = narration_text_for_scene(script, 2)
    assert "Scene one" in one
    assert "Scene two" in two
    assert "Scene two" not in one
