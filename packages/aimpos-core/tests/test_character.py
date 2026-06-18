"""Tests for character bible helpers."""

from aimpos_core.character import MAX_CHARACTERS_PER_PROJECT, format_character_bible


def test_format_character_bible_empty() -> None:
    assert format_character_bible([]) == ""


def test_format_character_bible_includes_fields() -> None:
    text = format_character_bible(
        [
            {
                "name": "Maya",
                "role": "protagonist",
                "description": "Marine biologist",
                "visual_traits": "Short black hair, lab coat",
                "personality_notes": "Curious and calm",
            }
        ]
    )
    assert "Maya" in text
    assert "protagonist" in text
    assert "lab coat" in text
    assert "Curious" in text


def test_max_characters_constant() -> None:
    assert MAX_CHARACTERS_PER_PROJECT == 3
