"""Episode pilot constants and metadata helpers (Phase 6 / SCR-2026-004)."""

from __future__ import annotations

MIN_EPISODES = 1
MAX_EPISODES = 10
DEFAULT_EPISODE_NUMBER = 1


def episode_number_from_metadata(metadata: dict | None) -> int | None:
    """Return 1-based episode number from asset metadata; None for legacy rows."""
    if not metadata:
        return None
    raw = metadata.get("episode_number")
    if raw is None:
        return None
    return int(raw)


def episode_zip_prefix(episode_number: int) -> str:
    """Deterministic ZIP path prefix for episode-scoped export (manifest v4)."""
    if episode_number < 1:
        raise ValueError("episode_number must be >= 1")
    return f"episodes/episode_{episode_number:02d}"
