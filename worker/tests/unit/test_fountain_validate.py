"""Unit tests for Fountain validation (US-14 / D-40)."""

from __future__ import annotations

import pytest

from app.agents.screenwriter.validate import (
    FountainValidationError,
    require_valid_fountain,
    validate_fountain,
)

VALID_ONE_SCENE = """Title: Mars Garden
Author: AIMPOS Screenwriter

INT. MARS HABITAT - NIGHT

Elara studies the bioluminescent sample under the lamp.

ELARA
We need more light on this.
"""

TWO_SCENES = """INT. ROOM - DAY

Action here.

BOB
Hello.

EXT. STREET - NIGHT

More action.

ALICE
Hi.
"""

NO_DIALOGUE = """INT. ROOM - DAY

Only action paragraphs without any speaking parts.
"""

NO_HEADING = """Title: Test

Just some prose without a scene heading.

BOB
Hello.
"""


def test_validate_accepts_valid_one_scene() -> None:
    result = validate_fountain(VALID_ONE_SCENE)
    assert result.ok is True
    assert result.scene_heading_count == 1
    assert result.scene_count == 1
    assert result.dialogue_count >= 1


def test_validate_rejects_zero_scene_headings() -> None:
    result = validate_fountain(NO_HEADING)
    assert result.ok is False
    assert result.scene_heading_count == 0
    assert "scene_heading_count == 0" in result.errors


def test_validate_rejects_scene_count_not_one() -> None:
    result = validate_fountain(TWO_SCENES)
    assert result.ok is False
    assert result.scene_count == 2
    assert any("scene_count != 1" in err for err in result.errors)


def test_validate_rejects_zero_dialogue() -> None:
    result = validate_fountain(NO_DIALOGUE)
    assert result.ok is False
    assert result.dialogue_count == 0
    assert "dialogue_count == 0" in result.errors


def test_validate_rejects_empty() -> None:
    result = validate_fountain("   ")
    assert result.ok is False
    assert result.scene_heading_count == 0


def test_require_valid_fountain_raises() -> None:
    with pytest.raises(FountainValidationError):
        require_valid_fountain(TWO_SCENES)


def test_accepts_int_ext_form() -> None:
    script = """INT/EXT. ROVER - CONTINUOUS

The rover stops.

MAYA
Contact.
"""
    result = validate_fountain(script)
    assert result.ok is True
    assert result.scene_count == 1
