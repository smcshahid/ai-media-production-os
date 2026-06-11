"""ComfyUI image-to-video enhancement path (US-18 phase 2) with mandatory fallback."""

from __future__ import annotations

import logging

from aimpos_config import Settings

logger = logging.getLogger(__name__)


class VideoI2VError(Exception):
    """ComfyUI i2v unavailable or failed — caller must fall back to slideshow."""


def try_comfyui_i2v(settings: Settings, png_frames: list[bytes]) -> bytes:
    """Attempt ComfyUI i2v; raises VideoI2VError on any failure (phase 2 stub)."""
    enabled = getattr(settings, "video_i2v_enabled", False)
    if not enabled:
        raise VideoI2VError("comfyui i2v disabled (video_i2v_enabled=false)")

    # Phase 2: pin workflow JSON and integrate gpu sequencer before enabling.
    raise VideoI2VError("comfyui i2v workflow not configured")
