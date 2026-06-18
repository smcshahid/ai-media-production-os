"""Unit tests for Fountain validation (US-14 / Phase 4 D-74)."""

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

THREE_SCENES = """INT. ROOM - DAY

Action one.

BOB
Hello.

EXT. STREET - NIGHT

Action two.

ALICE
Hi.

INT. LAB - DAWN

Action three.

CARL
Done.
"""

FOUR_SCENES = """INT. A - DAY

A talks.

AL
One.

EXT. B - DAY

B talks.

BO
Two.

INT. C - DAY

C talks.

CA
Three.

EXT. D - DAY

D talks.

DA
Four.
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


def test_validate_accepts_two_scenes() -> None:
    result = validate_fountain(TWO_SCENES)
    assert result.ok is True
    assert result.scene_count == 2


def test_validate_accepts_three_scenes() -> None:
    result = validate_fountain(THREE_SCENES)
    assert result.ok is True
    assert result.scene_count == 3


def test_validate_rejects_four_scenes() -> None:
    result = validate_fountain(FOUR_SCENES)
    assert result.ok is False
    assert result.scene_count == 4


def test_validate_rejects_zero_scene_headings() -> None:
    result = validate_fountain(NO_HEADING)
    assert result.ok is False
    assert result.scene_heading_count == 0
    assert "scene_heading_count == 0" in result.errors


def test_validate_expected_scene_count_mismatch() -> None:
    result = validate_fountain(TWO_SCENES, expected_scene_count=3)
    assert result.ok is False
    assert any("scene_count != 3" in err for err in result.errors)


def test_validate_rejects_zero_dialogue() -> None:
    result = validate_fountain(NO_DIALOGUE)
    assert result.ok is False
    assert result.dialogue_count == 0
    assert "dialogue_count == 0" in result.errors


def test_validate_rejects_empty() -> None:
    result = validate_fountain("   ")
    assert result.ok is False
    assert result.scene_heading_count == 0


def test_require_valid_fountain_raises_on_four_scenes() -> None:
    with pytest.raises(FountainValidationError):
        require_valid_fountain(FOUR_SCENES)


def test_accepts_int_ext_form() -> None:
    script = """INT/EXT. ROVER - CONTINUOUS

The rover stops.

MAYA
Contact.
"""
    result = validate_fountain(script)
    assert result.ok is True
    assert result.scene_count == 1
