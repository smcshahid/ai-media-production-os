"""US-18 slideshow renderer tests."""

from __future__ import annotations

import shutil

import pytest

from app.agents.video.slideshow import render_slideshow_mp4

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_render_slideshow_mp4_produces_valid_duration() -> None:
    frames = [PNG, PNG, PNG, PNG]
    mp4_bytes, probe = render_slideshow_mp4(frames)
    assert mp4_bytes[4:8] == b"ftyp"
    assert 15.0 <= probe.duration_sec <= 30.0
    assert probe.height <= 480


def test_render_slideshow_requires_four_frames() -> None:
    with pytest.raises(Exception):
        render_slideshow_mp4([PNG, PNG, PNG])
