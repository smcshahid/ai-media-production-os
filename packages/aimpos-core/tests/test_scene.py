"""Unit tests for aimpos_core scene helpers."""

from __future__ import annotations

import pytest

from aimpos_core.scene import extract_fountain_scene, scene_index_from_metadata


TWO_SCENES = """INT. ROOM - DAY

Action here.

BOB
Hello.

EXT. STREET - NIGHT

More action.

ALICE
Hi.
"""


def test_scene_index_from_metadata_defaults_to_one() -> None:
    assert scene_index_from_metadata(None) == 1
    assert scene_index_from_metadata({}) == 1
    assert scene_index_from_metadata({"scene_index": 2}) == 2


def test_extract_fountain_scene_first() -> None:
    block = extract_fountain_scene(TWO_SCENES, 1)
    assert "INT. ROOM" in block
    assert "EXT. STREET" not in block


def test_extract_fountain_scene_second() -> None:
    block = extract_fountain_scene(TWO_SCENES, 2)
    assert "EXT. STREET" in block
    assert "INT. ROOM" not in block


def test_extract_fountain_scene_out_of_range() -> None:
    with pytest.raises(ValueError):
        extract_fountain_scene(TWO_SCENES, 3)
