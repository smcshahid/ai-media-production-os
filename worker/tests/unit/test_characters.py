"""Worker character snapshot helpers (Phase 7.5)."""

from app.tools.characters import _profiles_from_snapshot


def test_profiles_from_snapshot_parses_dicts() -> None:
    raw = [
        {
            "id": "abc",
            "name": "Maya",
            "role": "protagonist",
            "description": "Biologist",
            "visual_traits": "Lab coat",
            "personality_notes": "Curious",
        }
    ]
    profiles = _profiles_from_snapshot(raw)
    assert len(profiles) == 1
    assert profiles[0]["name"] == "Maya"
    assert profiles[0]["visual_traits"] == "Lab coat"


def test_profiles_from_snapshot_empty() -> None:
    assert _profiles_from_snapshot(None) == []
    assert _profiles_from_snapshot([]) == []
