"""Tests for episode helpers (Phase 6)."""

from aimpos_core.episode import (
    DEFAULT_EPISODE_NUMBER,
    episode_number_from_metadata,
    episode_zip_prefix,
)


def test_episode_number_from_metadata_legacy() -> None:
    assert episode_number_from_metadata(None) is None
    assert episode_number_from_metadata({}) is None
    assert episode_number_from_metadata({"scene_index": 1}) is None


def test_episode_number_from_metadata_present() -> None:
    assert episode_number_from_metadata({"episode_number": 2}) == 2


def test_episode_zip_prefix() -> None:
    assert episode_zip_prefix(1) == "episodes/episode_01"
    assert episode_zip_prefix(12) == "episodes/episode_12"


def test_default_episode_number_constant() -> None:
    assert DEFAULT_EPISODE_NUMBER == 1
