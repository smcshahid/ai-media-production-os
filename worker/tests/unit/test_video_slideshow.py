"""US-18 slideshow renderer tests."""

from __future__ import annotations

import shutil
import struct
import zlib

import pytest

from app.agents.video.slideshow import render_slideshow_mp4


def _make_png(width: int = 64, height: int = 64, color: tuple[int, int, int] = (90, 120, 160)) -> bytes:
    """Build a minimal valid RGB PNG (stdlib only) so ffmpeg can decode it."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(color) * width
    raw = row * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


PNG = _make_png()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_render_slideshow_mp4_produces_valid_duration() -> None:
    frames = [PNG, PNG, PNG, PNG]
    mp4_bytes, probe = render_slideshow_mp4(frames)
    assert mp4_bytes[4:8] == b"ftyp"
    assert 15.0 <= probe.duration_sec <= 30.0
    # Cinematic upgrade renders at up to 720p (D-61).
    assert probe.height <= 720


def test_render_slideshow_requires_four_frames() -> None:
    with pytest.raises(Exception):
        render_slideshow_mp4([PNG, PNG, PNG])
